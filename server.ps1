$port = 8080
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")
try {
    $listener.Start()
} catch {
    Write-Error "Could not start listener on port $port. Is it already in use?"
    exit 1
}

Write-Host "Server started at http://localhost:$port/"
Write-Host "Press Ctrl+C to stop."

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response

    $path = $request.Url.LocalPath
    # Default to login.html if root is requested
    if ($path -eq "/") { $path = "/login.html" }
    
    # Remove leading slash for Join-Path
    if ($path.StartsWith("/")) { $path = $path.Substring(1) }
    
    $localPath = Join-Path $PWD $path
    
    if (Test-Path $localPath -PathType Leaf) {
        $content = [System.IO.File]::ReadAllBytes($localPath)
        $extension = [System.IO.Path]::GetExtension($localPath)
        
        switch ($extension) {
            ".html" { $response.ContentType = "text/html; charset=utf-8" }
            ".css"  { $response.ContentType = "text/css" }
            ".js"   { $response.ContentType = "application/javascript" }
            ".json" { $response.ContentType = "application/json" }
            ".png"  { $response.ContentType = "image/png" }
            ".jpg"  { $response.ContentType = "image/jpeg" }
            ".svg"  { $response.ContentType = "image/svg+xml" }
            default { $response.ContentType = "application/octet-stream" }
        }
        
        $response.ContentLength64 = $content.Length
        $response.OutputStream.Write($content, 0, $content.Length)
        Write-Host "200 $path"
    } else {
        $response.StatusCode = 404
        $notFound = [System.Text.Encoding]::UTF8.GetBytes("<h1>404 Not Found</h1><p>The file '$path' could not be found.</p>")
        $response.ContentType = "text/html"
        $response.ContentLength64 = $notFound.Length
        $response.OutputStream.Write($notFound, 0, $notFound.Length)
        Write-URL "404 $path"
    }
    
    $response.Close()
}
