@echo off
REM VDH Helpdesk App - Remove Pages Directory
REM This script will remove the pages/ folder causing sidebar links

echo ========================================
echo VDH Helpdesk - Remove Sidebar Links
echo ========================================
echo.

cd /d C:\Users\Admin\Documents\GitHub\vdh-helpdesk-app

echo Checking for pages directory...
echo.

if exist pages (
    echo FOUND: pages directory exists
    echo.
    echo Contents of pages directory:
    dir pages
    echo.
    echo.
    
    set /p confirm="Delete pages directory? (Y/N): "
    if /i "%confirm%"=="Y" (
        echo.
        echo Deleting pages directory...
        rmdir /s /q pages
        
        echo.
        echo Checking if deleted...
        if not exist pages (
            echo SUCCESS: pages directory removed!
            echo.
            echo Committing changes to Git...
            git add -A
            git commit -m "Remove pages directory causing sidebar navigation links"
            
            echo.
            echo Pushing to GitHub...
            git push origin main
            
            echo.
            echo ========================================
            echo DONE! 
            echo.
            echo The sidebar links should disappear after:
            echo 1. Azure redeploys (2-3 minutes)
            echo 2. You hard refresh the browser (Ctrl+Shift+R)
            echo ========================================
        ) else (
            echo ERROR: Failed to delete pages directory
            echo Please try manually: rmdir /s /q pages
        )
    ) else (
        echo Cancelled. No changes made.
    )
) else (
    echo.
    echo pages directory NOT found in this repository!
    echo.
    echo Current directory contents:
    dir /b
    echo.
    echo Checking on GitHub...
    echo Please verify at: https://github.com/CyberguysITSolutions/vdh-helpdesk-app
    echo.
    echo If you don't see a pages/ folder on GitHub, try:
    echo 1. Hard refresh browser: Ctrl+Shift+R
    echo 2. Clear browser cache
    echo 3. Wait for Azure deployment to complete
)

echo.
pause
