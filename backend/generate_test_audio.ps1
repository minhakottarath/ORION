Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile("test_voice.wav")
$s.Speak("what is the vibration alert threshold for titan eight hundred")
$s.Dispose()
Write-Host "Audio synthesized: test_voice.wav"
