import UIKit
import Speech
import AVFoundation
import Foundation

class ViewController: UIViewController, SFSpeechRecognizerDelegate {

    let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    let audioEngine = AVAudioEngine()
    var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    var recognitionTask: SFSpeechRecognitionTask?
    var finalRecognizedText: String = ""
    
    @IBOutlet weak var recognitionLabel: UILabel!
    @IBOutlet weak var microphoneButton: UIButton!

    override func viewDidLoad() {
        super.viewDidLoad()
        
        view.backgroundColor = UIColor.purple
        // Customize button appearance
        microphoneButton.layer.cornerRadius = 10
        microphoneButton.backgroundColor = UIColor.darkGray // Customize the color
        microphoneButton.setTitleColor(UIColor.white, for: .normal)
        
        // Add a subtle animation to the button
        microphoneButton.transform = CGAffineTransform(scaleX: 0.8, y: 0.8)
        UIView.animate(withDuration: 0.5) {
            self.microphoneButton.transform = .identity
        }
        speechRecognizer?.delegate = self

        SFSpeechRecognizer.requestAuthorization { (authStatus) in
            DispatchQueue.main.async {
                if authStatus == .authorized {
                    // Microphone access granted, configure your UI here.
                    self.microphoneButton.isEnabled = true
            }
            
            }
        }
    }

    @IBAction func startVoiceRecognition(_ sender: Any) {
        if audioEngine.isRunning {
            audioEngine.stop()
            recognitionRequest?.endAudio()
            microphoneButton.isEnabled = false
            microphoneButton.setTitle("Start Recording", for: .normal)
            sendRecognizedTextToServer()
            
            recognitionTask?.cancel()
            recognitionTask = nil
            finalRecognizedText = ""
            
            // Re-enable the "Start Recording" button
            microphoneButton.isEnabled = true
            audioEngine.stop()
            recognitionRequest?.endAudio()
        } else {
            startRecording()
            microphoneButton.setTitle("Stop Recording", for: .normal)
        }
    }

    func startRecording() {
        if let recognitionTask = recognitionTask {
            recognitionTask.cancel()
            self.recognitionTask = nil
        }
            
        // Reset the label text to empty
        DispatchQueue.main.async {
            self.recognitionLabel.text = ""
        }
        // Remove any existing tap before installing a new one
        audioEngine.inputNode.removeTap(onBus: 0)
        
        
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)

            recognitionRequest = SFSpeechAudioBufferRecognitionRequest()

            guard let recognitionRequest = recognitionRequest else { return }
            recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest, resultHandler: { (result, error) in
                if let result = result {
                    let recognizedText = result.bestTranscription.formattedString
                    self.finalRecognizedText = recognizedText
                    //print(self.finalRecognizedText)
                    DispatchQueue.main.async {
                        self.recognitionLabel.text = recognizedText
                            }
                } 
                })

            let inputNode = audioEngine.inputNode
            let recordingFormat = inputNode.outputFormat(forBus: 0)
            inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { (buffer, when) in
                recognitionRequest.append(buffer)
            }

            audioEngine.prepare()
            try audioEngine.start()
        } catch {
            // Handle errors
        }
    }
    func sendRecognizedTextToServer() {
        // URL to which you want to send the data
        let urlStr = "https://8f63-209-2-231-42.ngrok-free.app"
        
        // Create the URL object
        if let url = URL(string: urlStr) {
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            
            // Set the HTTP request header for JSON data
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            // Create a dictionary with the finalRecognizedText
            let jsonDictionary = ["recognizedText": finalRecognizedText]
            
            // Convert the dictionary to JSON data
            if let jsonData = try? JSONSerialization.data(withJSONObject: jsonDictionary) {
                // Set the JSON data as the request body
                request.httpBody = jsonData
                
                // Create a URLSession data task to send the request
                let task = URLSession.shared.dataTask(with: request) { (data, response, error) in
                    if let error = error {
                        print("Error sending POST request: \(error)")
                        return
                    }
                    
                    // Handle the response from the server if needed
                    if let data = data {
                        if let responseString = String(data: data, encoding: .utf8) {
                            print("Response from server: \(responseString)")
                        }
                    }
                }
                task.resume()
            }
        }
    }


}
