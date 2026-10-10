defmodule Example do
  use Phoenix.LiveView

  def mount(params, session, socket) do
    {:ok, App.Wizard.restore(socket, params, session)}
  end

  def handle_event("change", fields, socket) do
    {:noreply, App.Wizard.update(socket, fields)}
  end
end
