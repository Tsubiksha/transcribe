import React from "react";
import ChatMessage from "./ChatMessage";
import Icon from "./Icon";
import LoadingSpinner from "./LoadingSpinner";

export default function ChatBox({ messages, question, setQuestion, onSubmit, loading }) {
  return (
    <section className="panel flex min-h-[520px] flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 ? <p className="text-sm text-slate-500">Ask a question after selecting a source.</p> : messages.map((m, i) => <ChatMessage key={i} message={m} />)}
        {loading && (
          <div className="max-w-3xl rounded-lg border border-line bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
            Reading retrieved transcript chunks...
          </div>
        )}
      </div>
      <form onSubmit={onSubmit} className="mt-4 flex gap-2">
        <input className="field" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about this audio or video..." required />
        <button className="btn-primary shrink-0" disabled={loading}>{loading ? <LoadingSpinner /> : <Icon name="send" size={17} />} Send</button>
      </form>
    </section>
  );
}
