Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile("test_cat.wav")
$s.Speak("cat")
$s.Dispose()
Write-Host "Created test_cat.wav"
