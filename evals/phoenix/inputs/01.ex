defmodule Example do
  use Phoenix.LiveView

  def mount(_params, _session, socket), do: {:ok, assign(socket, help_open: false)}

  def render(assigns) do
    ~H"""
    <button phx-click="toggle_help">Help</button>
    <section id="help" hidden={!@help_open}>
      <p>Choose a file, then press Upload.</p>
    </section>
    """
  end

  def handle_event("toggle_help", _, socket) do
    {:noreply, update(socket, :help_open, &(!&1))}
  end
end
