/**
 * Platform-specific utilities for Windows
 * Handles screen share exclusion
 */

const { BrowserWindow } = require('electron');

function setWindowExStyle(window) {
    if (process.platform !== 'win32') {
        return;
    }

    try {
        // Get native window handle
        const hwnd = window.getNativeWindowHandle();

        // This would require native bindings to set WS_EX_TOOLWINDOW
        // For now, we'll use a simpler approach with setSkipTaskbar
        window.setSkipTaskbar(false);

        // Note: Full screen share exclusion on Windows requires native code
        // The window will still be visible in screen shares by default
        // For production, you'd need to use node-ffi or a native addon

        console.log('Windows-specific styling applied');
    } catch (error) {
        console.error('Error applying Windows styling:', error);
    }
}

module.exports = {
    setWindowExStyle,
};
