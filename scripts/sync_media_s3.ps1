# PowerShell script to sync media folder to S3
# Usage: .\sync_media_s3.ps1 -Destination s3://your-bucket/media/
param(
    [Parameter(Mandatory=$true)][string]$Destination
)

Write-Host "Syncing media/ to $Destination"
aws s3 sync .\media\ $Destination --acl private
Write-Host "Done."
