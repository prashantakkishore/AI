        const URL = "ws://localhost:9082";
        const video = document.getElementById("videoElement");
        const canvas = document.getElementById("canvasElement");
        const context = canvas.getContext("2d");
        const startButton = document.getElementById('startButton');
        const videoButton = document.getElementById('videoButton');
        const screenShareButton = document.getElementById('screenShareButton');


        let isListening = false;
        let sharingScreen = false;
        let isVideoOn = false;

        let stream = null;
        let currentFrameB64;
        let webSocket = null;
        let audioContext = null;
        let mediaRecorder = null;
        let processor = null;
        let pcmData = [];
        let accumulatedPcmData = [];
        let interval = null;
        let initialized = false;
        let audioInputContext;
        let workletNode;

        // Function to start the webcam
        async function startWebcam() {
            try {
                const constraints = {
                    video: {
                        width: {
                            max: 640
                        },
                        height: {
                            max: 480
                        },
                    },
                };

                stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
            } catch (err) {
                console.error("Error accessing the webcam: ", err);
            }
        }

        // Function to capture an image and convert it to base64
        function captureImage() {
            if (stream) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = canvas.toDataURL("image/jpeg").split(",")[1].trim();
                currentFrameB64 = imageData;
            }
        }



        function connect() {
            console.log("connecting: ", URL);

            webSocket = new WebSocket(URL);

            webSocket.onclose = (event) => {
                console.log("websocket closed: ", event);
                alert("Connection closed");
            };

            webSocket.onerror = (event) => {
                console.log("websocket error: ", event);
            };

            webSocket.onopen = (event) => {
                console.log("websocket open: ", event);
                sendInitialSetupMessage();
            };

            webSocket.onmessage = receiveMessage;
        }

        function sendInitialSetupMessage() {

            console.log("sending setup message");
            setup_client_message = {
                setup: {
                    generation_config: {
                        response_modalities: ["AUDIO"]
                    },
                },
            };

            webSocket.send(JSON.stringify(setup_client_message));
        }

        function sendAudioToTranscribe(b64PCM) {
                    if (webSocket == null) {
                        console.log("websocket not initialized");
                        return;
                    }

                    payload = {
                        realtime_input: {
                            media_chunks: [{
                                    mime_type: "audio/transcribe",
                                    data: b64PCM,
                                }
                            ],
                        },
                    };

                    webSocket.send(JSON.stringify(payload));
                    console.log("sent: ", payload);
                }

        function sendVoiceMessage(b64PCM) {
            if (webSocket == null) {
                console.log("websocket not initialized");
                return;
            }

            payload = {
                realtime_input: {
                    media_chunks: [{
                            mime_type: "audio/pcm",
                            data: b64PCM,
                        },
                        {
                            mime_type: "image/jpeg",
                            data: currentFrameB64,
                        },
                    ],
                },
            };

            webSocket.send(JSON.stringify(payload));
            console.log("sent: ", payload);
        }

        function sendTextMessage(txt) {
            if (webSocket == null) {
                console.log("websocket not initialized");
                return;
            }
            setup_client_message = {
                setup: {
                    generation_config: {
                        response_modalities: ["AUDIO"]
                    },
                },
            };

            webSocket.send(JSON.stringify(setup_client_message));
            payload = {
                realtime_input: {
                    media_chunks: [{
                        mime_type: "application/json",
                        data: txt
                    }],
                },
            };

            webSocket.send(JSON.stringify(payload));
            console.log("sent txt: ", payload);
        }

        function receiveMessage(event) {
            const messageData = JSON.parse(event.data);
            const response = new Response(messageData);

//            if (response.text) {
//                displayMessage("GEMINI Text: " + response.text);
//            }
            if (response.json) {
                displayChatResponse(response.json);
            }
            if (response.audioData) {
                accumulatedPcmData.push(messageData.audio);
                injestAudioChuckToPlay(response.audioData);
            }
            if (response.endOfTurn) {
                    if (accumulatedPcmData.length > 0) {
                      try {
                        const fullPcmData = accumulatedPcmData.join('');

                        sendAudioToTranscribe(fullPcmData);
                        accumulatedPcmData = []; // Clear accumulated data
                      } catch (error) {
                        console.error("[WebSocket] Transcription error:", error);
                      }
                    }
                  }

                  if (response.transcribeJson) {
                                  console.log("Transcribed Text " + response.transcribeJson)
                                  appendToTextArea("AI", response.transcribeJson)
                              }
        }


        async function initializeAudioContext() {
            if (initialized) return;

            audioInputContext = new(window.AudioContext ||
                window.webkitAudioContext)({
                sampleRate: 24000
            });
            await audioInputContext.audioWorklet.addModule("pcm-processor.js");
            workletNode = new AudioWorkletNode(audioInputContext, "pcm-processor");
            workletNode.connect(audioInputContext.destination);
            initialized = true;
        }


        function base64ToArrayBuffer(base64) {
            const binaryString = window.atob(base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            return bytes.buffer;
        }

        function convertPCM16LEToFloat32(pcmData) {
            const inputArray = new Int16Array(pcmData);
            const float32Array = new Float32Array(inputArray.length);

            for (let i = 0; i < inputArray.length; i++) {
                float32Array[i] = inputArray[i] / 32768;
            }

            return float32Array;
        }


        async function injestAudioChuckToPlay(base64AudioChunk) {
            try {
                if (!initialized) {
                    await initializeAudioContext();
                }

                if (audioInputContext.state === "suspended") {
                    await audioInputContext.resume();
                }
                const arrayBuffer = base64ToArrayBuffer(base64AudioChunk);
                const float32Data = convertPCM16LEToFloat32(arrayBuffer);

                workletNode.port.postMessage(float32Data);
            } catch (error) {
                console.error("Error processing audio chunk:", error);
            }
        }

        function uint8ArrayToString(uint8Array, chunkSize = 1024) {
            let str = '';
            for (let i = 0; i < uint8Array.length; i += chunkSize) {
                const chunk = uint8Array.subarray(i, i + chunkSize);
                str += String.fromCharCode.apply(null, chunk);
            }
            return str;
        }

        function recordChunk() {
            const buffer = new ArrayBuffer(pcmData.length * 2);
            const view = new DataView(buffer);
            pcmData.forEach((value, index) => {
                view.setInt16(index * 2, value, true);
            });
            const int8Buffer = new Uint8Array(buffer);

            // Convert Uint8Array to a binary string. Crucial step!
            let binary = '';
            const len = int8Buffer.byteLength;
            for (let i = 0; i < len; i++) {
                binary += String.fromCharCode(int8Buffer[i]);
            }

            const base64 = btoa(binary);  // Now correctly base64 encodes the binary data.
            sendVoiceMessage(base64);
            pcmData = [];
        }

        // Function to start screen capture
        async function startScreenShare() {
            try {
                stream = await navigator.mediaDevices.getDisplayMedia({
                    video: {
                        width: {
                            max: 640
                        },
                        height: {
                            max: 480
                        },
                    },
                });

                video.srcObject = stream;
                await new Promise(resolve => {
                    video.onloadedmetadata = () => {
                        console.log("video loaded metadata");
                        resolve();
                    }
                });

            } catch (err) {
                console.error("Error accessing the screen: ", err);
            }
        }

        function toggleAudio() {

            if (!isListening) {
                startAudioInput();
            } else {
                stopAudioInput();
            }
            isListening = !isListening;
        }

        async function startAudioInput() {
            audioContext = new AudioContext({
                sampleRate: 16000,
            });

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                },
            });

            const source = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                const inputData = e.inputBuffer.getChannelData(0);
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    pcm16[i] = inputData[i] * 0x7fff;
                }
                pcmData.push(...pcm16);
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            interval = setInterval(recordChunk, 3000);
        }

        function stopAudioInput() {
            if (processor) {
                processor.disconnect();
            }
            if (audioContext) {
                audioContext.close();
            }

            clearInterval(interval);
        }

        function displayChatResponse(message) {
            console.log(message);
            const textarea = document.getElementById('myTextarea');
            // Append the text to the textarea
            textarea.innerHTML += message; // Adding a newline character
        }

        function displayMessage(message) {
            console.log(message);
            addParagraphToDiv("chatLog", message);
        }

        function appendToTextArea(type, text) {
                    const textarea = document.getElementById('myTextarea');
                    textarea.addEventListener('input', function() {

                     textarea.scrollTop = textarea.scrollHeight;  // Scroll to the bottom

                    });
            // 2. Create the div and its content
              const div = document.createElement('div');

              const spanImage = document.createElement('span');
              const image = document.createElement('img');
//              image.src = "img.png";
              image.src = type == "AI"? "images.jpg": "user.png";
              image.alt = text; // Accessibility! Use the text as the alt text.  Adjust if a better alt text is known
              image.height = 35; // Set the image height
                image.width = 50;
              spanImage.appendChild(image);

              const spanText = document.createElement('span');
              spanText.textContent = text;  // Safer than innerHTML for plain text


              div.appendChild(spanImage);
              div.appendChild(spanText);

              // 3. Convert the div to a string representation (HTML)
              const divHtml = div.outerHTML;
                                    /// 4. Insert the HTML string into the textarea
//                                       const currentText = textarea.value;
//                                       textarea.value = currentText + divHtml;
textarea.innerHTML = divHtml + textarea.innerHTML
                }


        function addParagraphToDiv(divId, text) {
            const newParagraph = document.createElement("p");
            newParagraph.textContent = text;
            const div = document.getElementById(divId);
            div.appendChild(newParagraph);
        }


        class Response {
            constructor(data) {
                this.text = null;
                this.json = null;
                this.audioData = null;
                this.endOfTurn = null;
                this.transcribeJson = null;

                if (data.text) {
                    this.text = data.text
                }
                if (data.json) {
                    this.json = data.json
                }

                if (data.audio) {
                    this.audioData = data.audio;
                }

                if (data.serverContent?.turnComplete) {
                    this.endOfTurn = true;
                }
                 if (data.transcribe_json) {
                     this.transcribeJson = data.transcribe_json;
                 }
            }
        }

        window.addEventListener("load", async () => {
            connect();
        });
        screenShareButton.addEventListener("click", async () => {
            screenShareButton.classList.toggle("listening");
            if(!sharingScreen) {
                await startScreenShare();
                setInterval(captureImage, 3000);
            } else {
                const videoElement = document.getElementById('videoElement');
                                videoElement.autoplay = false;
                                videoElement.load();
            }
            sharingScreen = !sharingScreen;
        });
        startButton.addEventListener('click', toggleAudio);
        startButton.addEventListener("click", function() {
            startButton.classList.toggle("listening");
        });
        videoButton.addEventListener("click", function() {
            videoButton.classList.toggle("listening");
            if (!isVideoOn) {
                const videoElement = document.getElementById('videoElement');
                videoElement.autoplay = true;
                videoElement.load();
                startWebcam();
                setInterval(captureImage, 3000);
            } else {
                const videoElement = document.getElementById('videoElement');
                videoElement.autoplay = false;
                videoElement.load();
            }
            isVideoOn = !isVideoOn;
        });

        document.getElementById('myInput').addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault(); // Prevent default behavior of the enter key

                const inputText = this.value;
                appendToTextArea("User", inputText)
                sendTextMessage(this.value)
                this.value = ''; // Clear the input field
            }
        });

