/**
 * Electron Main Process
 * Creates transparent overlay window with always-on-top functionality
 */

const { app, BrowserWindow, screen, ipcMain, globalShortcut } = require('electron');
const path = require('path');

let mainWindow = null;

function createWindow() {
  // Get primary display dimensions
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 400,
    height: 600,
    x: width - 420,  // Position on right side of screen
    y: 20,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    hasShadow: false,
    resizable: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true,
    }
  });

  // Load the index.html
  mainWindow.loadFile('index.html');

  // Open DevTools in development mode
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  // Platform-specific configurations for screen share exclusion
  if (process.platform === 'win32') {
    // Windows: Set extended window style to exclude from screen capture
    const { setWindowExStyle } = require('./platform/windows');
    setWindowExStyle(mainWindow);
  } else if (process.platform === 'darwin') {
    // macOS: Set window level to exclude from screen sharing
    mainWindow.setWindowLevel('pop-up-menu');
  }

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(() => {
  createWindow();

  // Register global shortcuts
  globalShortcut.register('CommandOrControl+Shift+I', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });

  globalShortcut.register('CommandOrControl+Shift+Q', () => {
    app.quit();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll();
});

// IPC handlers
ipcMain.on('minimize-window', () => {
  if (mainWindow) {
    mainWindow.minimize();
  }
});

ipcMain.on('close-window', () => {
  if (mainWindow) {
    mainWindow.close();
  }
});

ipcMain.on('toggle-always-on-top', (event, flag) => {
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(flag);
  }
});
