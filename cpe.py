from flask import Flask, render_template_string, Response, request, jsonify, redirect, url_for
import cozmo
import io
from PIL import ImageDraw
import threading

app = Flask(__name__)
cozmo_robot = None
shift_pressed = False  # Variable to track if Shift is pressed

@app.route('/')
def index():
    index_page = '''
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Cozmo Control</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: #87CEFA;  /* Light blue background */
            }
            h1, h2 {
                color: #333;
            }
            img {
                border: 5px solid blue; /* Blue frame for the camera feed */
                border-radius: 8px;
            }
            button {
                background-color: blue; /* Blue buttons */
                color: white;
                padding: 10px 20px;
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button.stop {
                background-color: red; /* Red stop button */
            }
            button:hover {
                opacity: 0.8;
            }
            input[type="text"] {
                padding: 10px;
                font-size: 16px;
                width: 300px;
                margin: 10px;
                border-radius: 5px;
                border: 1px solid #ccc;
            }
            #deadMessage {
                color: red;
                font-size: 24px;
                font-weight: bold;
                margin-top: 50px;
            }
            .green-hotbar {
                background-color: green;
                padding: 10px;
                margin: 10px 0;
                display: flex;
                justify-content: center;
                border-radius: 8px;
                flex-wrap: wrap;
            }
            .green-hotbar button {
                background-color: #4CAF50; /* Green buttons */
                margin: 5px;
            }
            .stylized-object {
                background-color: #00008B;  /* Dark blue stylized object */
                width: 100px;
                height: 100px;
                margin: 20px auto;
                border-radius: 50%;
            }
        </style>
      </head>
      <body>
        <h1>Control Cozmo</h1>
        <div class="stylized-object"></div>
        <img id="cozmoFeed" src="{{ url_for('video_feed') }}" width="640" height="480"><br>

        <div id="deadMessage"></div>

        <button onclick="sendCommand('forward')">Move Forward (Z)</button>
        <button onclick="sendCommand('backward')">Move Backward (S)</button>
        <button onclick="sendCommand('left')">Turn Left (Q)</button>
        <button onclick="sendCommand('right')">Turn Right (D)</button>
        <button onclick="sendCommand('stop')" class="stop">Stop</button><br><br>

        <button onclick="sendCommand('lift_up')">Lift Up (R)</button>
        <button onclick="sendCommand('lift_down')">Lift Down (F)</button><br>
        <button onclick="sendCommand('head_up')">Head Up (T)</button>
        <button onclick="sendCommand('head_down')">Head Down (G)</button><br><br>

        <h2>Animations</h2>
        <select id="animationSelect">
            <option value="anim_bored_02">Bored 02</option>
            <option value="anim_poked_giggle">Poked Giggle</option>
            <option value="anim_pounce_success_02">Pounce Success 02</option>
            <option value="anim_bored_event_02">Bored Event 02</option>
            <option value="anim_bored_event_03">Bored Event 03</option>
            <option value="anim_petdetection_cat_01">Pet Detection Cat 01</option>
            <option value="anim_petdetection_dog_03">Pet Detection Dog 03</option>
            <option value="anim_reacttoface_unidentified_02">React to Face Unidentified 02</option>
            <option value="anim_upgrade_reaction_lift_01">Upgrade Reaction Lift 01</option>
            <option value="anim_speedtap_wingame_intensity02_01">Speed Tap Win Game Intensity 02</option>
        </select>
        <button onclick="playSelectedAnimation()">Play Animation</button><br><br>

        <h2>Additional Features</h2>
        <button onclick="sendCommand('headlight_on')">HeadLight On</button>
        <button onclick="sendCommand('headlight_off')">HeadLight Off</button>
        <button onclick="sendCommand('debug_annotation')">Debug Annotation</button>
        <button onclick="sendCommand('freeplay')">FreePlay Mode</button>
        <button onclick="sendCommand('freeplay_off')">Stop FreePlay Mode</button><br><br>

        <div class="green-hotbar">
            <button onclick="sendCommand('anim_bored')">Sad</button>
            <button onclick="sendCommand('anim_happy')">Happy</button>
            <button onclick="sendCommand('anim_sneeze')">Sneeze</button>
            <button onclick="sendCommand('anim_laugh')">Laughing</button>
            <button onclick="sendCommand('anim_random')">Random Animal Imitation</button>
        </div>

        <h2>Mouse Look</h2>
        <button onclick="toggleMouseLook()">Toggle Mouse Look (A)</button><br><br>

        <h2>Text-to-Speech</h2>
        <input type="text" id="speechText" placeholder="Enter text for Cozmo to speak">
        <button onclick="speakText()">Speak</button><br><br>

        <!-- CodeLab button -->
        <button onclick="window.location.href='/everything_else'">CodeLab</button>

        <script>
            let mouseLookEnabled = false;
            let shiftPressed = false;  // Variable to track if Shift is pressed

            function sendCommand(command) {
                fetch('/control/' + command + (shiftPressed ? '_fast' : ''));
            }

            function playSelectedAnimation() {
                var selectedAnimation = document.getElementById("animationSelect").value;
                sendCommand(selectedAnimation);
            }

            function speakText() {
                var text = document.getElementById("speechText").value;
                fetch('/speak?text=' + encodeURIComponent(text));
            }

            function toggleMouseLook() {
                mouseLookEnabled = !mouseLookEnabled;
                if (mouseLookEnabled) {
                    document.body.requestPointerLock();
                    document.body.style.cursor = "crosshair"; // Change cursor to crosshair
                } else {
                    document.exitPointerLock();
                    document.body.style.cursor = "default"; // Revert cursor to default
                }
            }

            function handleMouseMove(event) {
                if (mouseLookEnabled) {
                    let deltaX = event.movementX || event.mozMovementX || event.webkitMovementX || 0;
                    let deltaY = event.movementY || event.mozMovementY || event.webkitMovementY || 0;

                    fetch(`/camera_control?dx=${deltaX}&dy=${deltaY}`);
                }
            }

            function checkCozmoFeed() {
                var cozmoFeed = document.getElementById("cozmoFeed");
                cozmoFeed.onerror = function() {
                    document.getElementById("deadMessage").innerText = "Cozmo has died lol";
                    cozmoFeed.style.display = 'none';
                };
            }

            document.addEventListener('DOMContentLoaded', function() {
                checkCozmoFeed();
                document.addEventListener('mousemove', handleMouseMove);
            });

            document.addEventListener('keydown', function(event) {
                if (event.key === 'a') {
                    toggleMouseLook();
                }

                if (event.key === 'Shift') {
                    shiftPressed = true;
                }

                if (event.key === 'z') {
                    sendCommand('forward');
                } else if (event.key === 's') {
                    sendCommand('backward');
                } else if (event.key === 'q') {
                    sendCommand('left');
                } else if (event.key === 'd') {
                    sendCommand('right');
                } else if (event.key === 'r') {
                    sendCommand('lift_up');
                } else if (event.key === 'f') {
                    sendCommand('lift_down');
                } else if (event.key === 't') {
                    sendCommand('head_up');
                } else if (event.key === 'g') {
                    sendCommand('head_down');
                }
            });

            document.addEventListener('keyup', function(event) {
                if (event.key === 'Shift') {
                    shiftPressed = false;
                }

                if (['z', 'q', 'd', 's', 'r', 'f', 't', 'g'].includes(event.key)) {
                    sendCommand('stop');
                }
            });
        </script>
      </body>
    </html>
    '''
    return render_template_string(index_page)

@app.route('/everything_else')
def everything_else():
    blockly_page = '''
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Blockly Code Lab</title>
        <script src="https://unpkg.com/blockly/blockly.min.js"></script>
        <script src="https://unpkg.com/blockly/python.min.js"></script>
        <script>
          Blockly.Blocks['cozmo_drive_straight'] = {
            init: function() {
              this.appendDummyInput()
                  .appendField("Drive Cozmo straight for")
                  .appendField(new Blockly.FieldNumber(100), "DISTANCE")
                  .appendField("mm at speed")
                  .appendField(new Blockly.FieldNumber(50), "SPEED")
                  .appendField("mm/s");
              this.setPreviousStatement(true, null);
              this.setNextStatement(true, null);
              this.setColour(230);
              this.setTooltip("Drive Cozmo straight");
              this.setHelpUrl("");
            }
          };

          Blockly.Python['cozmo_drive_straight'] = function(block) {
            var distance = block.getFieldValue('DISTANCE');
            var speed = block.getFieldValue('SPEED');
            var code = `cozmo_robot.drive_straight(cozmo.util.Distance(mm=${distance}), cozmo.util.Speed(mmps=${speed})).wait_for_completed()\n`;
            return code;
          };

          // Add other Cozmo blocks for animations, movements, actions, and sensors here

          function generateCode() {
            var code = Blockly.Python.workspaceToCode(workspace);
            document.getElementById('codeOutput').innerText = code;
            sendCodeToServer(code);
          }

          function sendCodeToServer(code) {
            fetch('/run_code', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({code: code})
            })
            .then(response => response.json())
            .then(data => {
              alert("Server Response: " + data.result);
            });
          }

          window.addEventListener('load', function() {
            var workspace = Blockly.inject('blocklyDiv', {
              toolbox: document.getElementById('toolbox')
            });
          });
        </script>
      </head>
      <body>
        <h1>Control Cozmo with Blockly</h1>
        <div id="blocklyDiv" style="height: 480px; width: 600px;"></div>
        <xml id="toolbox" style="display: none">
          <block type="cozmo_drive_straight"></block>
          <!-- Add other Cozmo blocks here -->
        </xml>
        <button onclick="generateCode()">Generate Python Code</button>
        <pre id="codeOutput"></pre>
      </body>
    </html>
    '''
    return render_template_string(blockly_page)

@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.get_json()
    code = data.get('code', '')

    # Run the code (be careful with executing code directly for security reasons)
    try:
        exec_locals = {}
        exec(code, globals(), exec_locals)
        return jsonify({'result': 'Code executed successfully'})
    except Exception as e:
        return jsonify({'result': str(e)})

def generate_video_stream():
    while True:
        if cozmo_robot:
            image = cozmo_robot.world.latest_image
            if image is not None:
                img = image.raw_image

                # Detect faces and draw a green rectangle around them
                draw = ImageDraw.Draw(img)
                for face in cozmo_robot.world.visible_faces:
                    box = face.face_bounds
                    draw.rectangle(((box.left, box.top), (box.right, box.bottom)), outline="green", width=5)

                # Convert image to bytes and yield it
                byte_array = io.BytesIO()
                img.save(byte_array, format='JPEG')
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + byte_array.getvalue() + b'\r\n')
        else:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control/<command>')
def control(command):
    if cozmo_robot:
        speed = 50 if 'fast' not in command else 100  # Set speed to 100 if Shift is pressed
        if 'forward' in command:
            cozmo_robot.drive_wheels(speed, speed)
        elif 'backward' in command:
            cozmo_robot.drive_wheels(-speed, -speed)
        elif 'left' in command:
            cozmo_robot.drive_wheels(-speed, speed)
        elif 'right' in command:
            cozmo_robot.drive_wheels(speed, -speed)
        elif 'stop' in command:
            cozmo_robot.stop_all_motors()
        elif 'lift_up' in command:
            cozmo_robot.move_lift(1.0)
        elif 'lift_down' in command:
            cozmo_robot.move_lift(-1.0)
        elif 'head_up' in command:
            cozmo_robot.move_head(1.0)
        elif 'head_down' in command:
            cozmo_robot.move_head(-1.0)
        elif command in [
            'anim_bored_02', 'anim_poked_giggle', 'anim_pounce_success_02',
            'anim_bored_event_02', 'anim_bored_event_03', 'anim_petdetection_cat_01',
            'anim_petdetection_dog_03', 'anim_reacttoface_unidentified_02',
            'anim_upgrade_reaction_lift_01', 'anim_speedtap_wingame_intensity02_01'
        ]:
            cozmo_robot.play_anim(name=command).wait_for_completed()
        elif command == 'headlight_on':
            cozmo_robot.set_head_light(True)
        elif command == 'headlight_off':
            cozmo_robot.set_head_light(False)
        elif command == 'debug_annotation':
            cozmo_robot.enable_all_debug_annotations()
        elif command == 'freeplay':
            cozmo_robot.start_freeplay_behaviors()
        elif command == 'freeplay_off':
            cozmo_robot.stop_freeplay_behaviors()
    return ('', 204)

@app.route('/camera_control')
def camera_control():
    dx = float(request.args.get('dx', 0))
    dy = float(request.args.get('dy', 0))

    if cozmo_robot:
        current_head_angle = cozmo_robot.head_angle.radians
        new_head_angle = current_head_angle + (dy * 0.005)  # Adjust sensitivity here
        cozmo_robot.set_head_angle(cozmo.robot.MIN_HEAD_ANGLE.radians if new_head_angle < cozmo.robot.MIN_HEAD_ANGLE.radians else new_head_angle if new_head_angle <= cozmo.robot.MAX_HEAD_ANGLE.radians else cozmo.robot.MAX_HEAD_ANGLE.radians).wait_for_completed()

        # Optionally, control Cozmo's body yaw to simulate full camera movement
        if dx != 0:
            cozmo_robot.turn_in_place(cozmo.util.degrees(dx * 0.5)).wait_for_completed()  # Adjust sensitivity here

    return ('', 204)

@app.route('/speak')
def speak():
    text = request.args.get('text', '')
    if cozmo_robot and text:
        cozmo_robot.say_text(text).wait_for_completed()
    return ('', 204)

def cozmo_program(robot: cozmo.robot.Robot):
    global cozmo_robot
    cozmo_robot = robot  # Assign the robot directly
    cozmo_robot.camera.image_stream_enabled = True
    app.run(host='0.0.0.0', port=5000)

cozmo.run_program(cozmo_program)
