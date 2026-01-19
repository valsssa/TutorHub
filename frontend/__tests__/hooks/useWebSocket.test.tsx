import { renderHook, act, waitFor } from "@testing-library/react";
import { useWebSocket } from "@/hooks/useWebSocket";
import Cookies from "js-cookie";

// Mock dependencies
jest.mock("js-cookie");
jest.mock("@/lib/logger", () => ({
  createLogger: () => ({
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn(),
  }),
}));

// Mock WebSocket
class MockWebSocket {
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  readyState: number = 0;
  CONNECTING = 0;
  OPEN = 1;
  CLOSING = 2;
  CLOSED = 3;

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = 1;
      this.onopen?.(new Event("open"));
    }, 10);
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = 3;
    this.onclose?.(new CloseEvent("close"));
  }
}

global.WebSocket = MockWebSocket as any;

describe("useWebSocket hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue("mock-token");
  });

  it("initializes with disconnected state", () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.isConnected).toBe(false);
    expect(result.current.lastMessage).toBeNull();
  });

  it("connects to WebSocket when token is available", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it("does not connect when token is missing", () => {
    (Cookies.get as jest.Mock).mockReturnValue(null);

    const { result } = renderHook(() => useWebSocket());

    expect(result.current.isConnected).toBe(false);
  });

  it("receives messages", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const mockMessage = {
      type: "new_message",
      message_id: 1,
      sender_id: 2,
      message: "Test message",
    };

    act(() => {
      const ws = (global.WebSocket as any).mock.instances[0];
      ws.onmessage(
        new MessageEvent("message", {
          data: JSON.stringify(mockMessage),
        })
      );
    });

    await waitFor(() => {
      expect(result.current.lastMessage).toEqual(mockMessage);
    });
  });

  it("sends typing indicator", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const sendSpy = jest.spyOn(MockWebSocket.prototype, "send");

    act(() => {
      result.current.sendTyping?.(5);
    });

    expect(sendSpy).toHaveBeenCalledWith(
      JSON.stringify({ type: "typing", recipient_id: 5 })
    );
  });

  it("sends custom messages", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const sendSpy = jest.spyOn(MockWebSocket.prototype, "send");

    const customMessage = { type: "custom", data: "test" };

    act(() => {
      result.current.sendMessage?.(customMessage);
    });

    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify(customMessage));
  });

  it("reconnects on connection loss", async () => {
    jest.useFakeTimers();

    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate connection loss
    act(() => {
      const ws = (global.WebSocket as any).mock.instances[0];
      ws.onclose(new CloseEvent("close"));
    });

    expect(result.current.isConnected).toBe(false);

    // Wait for reconnect attempt
    act(() => {
      jest.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    jest.useRealTimers();
  });

  it("handles connection errors", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    act(() => {
      const ws = (global.WebSocket as any).mock.instances[0];
      ws.onerror(new Event("error"));
    });

    // Connection should still be tracked correctly
    expect(result.current.isConnected).toBe(true);
  });

  it("cleans up on unmount", async () => {
    const { result, unmount } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const closeSpy = jest.spyOn(MockWebSocket.prototype, "close");

    unmount();

    expect(closeSpy).toHaveBeenCalled();
  });

  it("handles presence check", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const sendSpy = jest.spyOn(MockWebSocket.prototype, "send");

    act(() => {
      result.current.sendMessage?.({
        type: "presence_check",
        user_ids: [1, 2, 3],
      });
    });

    expect(sendSpy).toHaveBeenCalledWith(
      JSON.stringify({ type: "presence_check", user_ids: [1, 2, 3] })
    );
  });

  it("handles message delivery acknowledgment", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const deliveryMessage = {
      type: "delivery_receipt",
      message_id: 1,
      recipient_id: 2,
      state: "delivered",
    };

    act(() => {
      const ws = (global.WebSocket as any).mock.instances[0];
      ws.onmessage(
        new MessageEvent("message", {
          data: JSON.stringify(deliveryMessage),
        })
      );
    });

    await waitFor(() => {
      expect(result.current.lastMessage).toEqual(deliveryMessage);
    });
  });

  it("handles read receipt", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const readMessage = {
      type: "message_read",
      message_id: 1,
      reader_id: 2,
      state: "read",
    };

    act(() => {
      const ws = (global.WebSocket as any).mock.instances[0];
      ws.onmessage(
        new MessageEvent("message", {
          data: JSON.stringify(readMessage),
        })
      );
    });

    await waitFor(() => {
      expect(result.current.lastMessage).toEqual(readMessage);
    });
  });

  it("handles message deleted event", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const deletedMessage = {
      type: "message_deleted",
      message_id: 1,
      deleted_by: 2,
    };

    act(() => {
      const ws = (global.WebSocket as any).mock.instances[0];
      ws.onmessage(
        new MessageEvent("message", {
          data: JSON.stringify(deletedMessage),
        })
      );
    });

    await waitFor(() => {
      expect(result.current.lastMessage).toEqual(deletedMessage);
    });
  });

  it("handles message edited event", async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const editedMessage = {
      type: "message_edited",
      message_id: 1,
      new_content: "Updated message",
      edited_by: 2,
    };

    act(() => {
      const ws = (global.WebSocket as any).mock.instances[0];
      ws.onmessage(
        new MessageEvent("message", {
          data: JSON.stringify(editedMessage),
        })
      );
    });

    await waitFor(() => {
      expect(result.current.lastMessage).toEqual(editedMessage);
    });
  });
});
