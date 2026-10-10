defmodule Example do
  use Phoenix.LiveView

  def handle_event("open_panel", params, socket) do
    App.Panels.open(params, socket)
  end
end
