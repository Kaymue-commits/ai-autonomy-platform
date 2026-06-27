Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create bitmap
$bitmap = New-Object System.Drawing.Bitmap(1920, 1080)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)

# Capture screen
$graphics.CopyFromScreen(0, 0, 0, 0, [System.Drawing.Size]::new(1920, 1080))

# Save to file
$bitmap.Save("D:\Design\ai-autonomy-platform\screenshot.png", [System.Drawing.Imaging.ImageFormat]::Png)

# Cleanup
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "Screenshot saved to D:\Design\ai-autonomy-platform\screenshot.png"
