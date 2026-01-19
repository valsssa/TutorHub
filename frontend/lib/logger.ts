/**
 * Frontend logging utility with stderr output
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
  data?: any;
}

class Logger {
  private level: LogLevel;
  private enabledLevels: Set<LogLevel>;

  constructor() {
    // Get log level from environment, default to INFO
    const envLevel = process.env.NEXT_PUBLIC_LOG_LEVEL || 'INFO';
    this.level = LogLevel[envLevel as keyof typeof LogLevel] || LogLevel.INFO;

    // Set enabled levels based on current level
    this.enabledLevels = new Set<LogLevel>();
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
    const currentIndex = levels.indexOf(this.level);

    for (let i = currentIndex; i < levels.length; i++) {
      this.enabledLevels.add(levels[i]);
    }
  }

  private formatLogEntry(level: LogLevel, module: string, message: string, data?: any): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      module,
      message,
      data,
    };
  }

  private log(level: LogLevel, module: string, message: string, data?: any): void {
    if (!this.enabledLevels.has(level)) {
      return;
    }

    const entry = this.formatLogEntry(level, module, message, data);
    const logMessage = `${entry.timestamp} - ${entry.module} - ${entry.level} - ${entry.message}`;

    // Output to console.error (stderr)
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(logMessage, data || '');
        break;
      case LogLevel.INFO:
        console.info(logMessage, data || '');
        break;
      case LogLevel.WARN:
        console.warn(logMessage, data || '');
        break;
      case LogLevel.ERROR:
        console.error(logMessage, data || '');
        break;
    }
  }

  debug(module: string, message: string, data?: any): void {
    this.log(LogLevel.DEBUG, module, message, data);
  }

  info(module: string, message: string, data?: any): void {
    this.log(LogLevel.INFO, module, message, data);
  }

  warn(module: string, message: string, data?: any): void {
    this.log(LogLevel.WARN, module, message, data);
  }

  error(module: string, message: string, data?: any): void {
    this.log(LogLevel.ERROR, module, message, data);
  }
}

// Export singleton instance
export const logger = new Logger();

// Export helper function to create module-specific loggers
export function createLogger(module: string) {
  return {
    debug: (message: string, data?: any) => logger.debug(module, message, data),
    info: (message: string, data?: any) => logger.info(module, message, data),
    warn: (message: string, data?: any) => logger.warn(module, message, data),
    error: (message: string, data?: any) => logger.error(module, message, data),
  };
}
