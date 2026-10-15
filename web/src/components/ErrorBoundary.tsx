import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State { error: Error | null }

/** Shows a recovery screen instead of a blank page if part of the interface crashes. */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('PC-Sahayak interface error:', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="app">
        <div className="loading" role="alert">
          <div style={{ textAlign: 'center', maxWidth: 440, display: 'grid', gap: 12, justifyItems: 'center' }}>
            <p style={{ margin: 0, fontWeight: 700 }}>Something went wrong in PC-Sahayak.</p>
            <p style={{ margin: 0, fontSize: 14 }}>
              Your chats are safe. Reload the page; if this keeps happening, close the PC-Sahayak window and start it again.
            </p>
            <button className="ghost" type="button" onClick={() => window.location.reload()}>Reload</button>
          </div>
        </div>
      </div>
    );
  }
}
