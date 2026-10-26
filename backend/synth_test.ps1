param([string]$text = "cat", [string]$file = "test_cat.wav")
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile($file)
$s.Speak($text)
$s.Dispose()
Write-Host "Created $file with text: $text"
