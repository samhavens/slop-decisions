defmodule Example do
  use Phoenix.LiveView
  @moduledoc "Two-step signup: retain the name from step one until the user submits step two."

  def mount(_params, _session, socket) do
    {:ok, assign(socket, step: 1, name: "", email: "")}
  end

  def render(assigns) do
    ~H"""
    <form id="signup" phx-change="validate" phx-submit={if @step == 1, do: "next", else: "save"}>
      <input :if={@step == 1} name="signup[name]" value={@name} />
      <input :if={@step == 2} name="signup[email]" value={@email} />
      <button type="submit">Continue</button>
    </form>
    """
  end

  def handle_event("validate", %{"signup" => fields}, socket) do
    {:noreply, assign(socket,
      name: Map.get(fields, "name", socket.assigns.name),
      email: Map.get(fields, "email", socket.assigns.email))}
  end

  def handle_event("next", %{"signup" => %{"name" => name}}, socket) do
    {:noreply, assign(socket, step: 2, name: name)}
  end

  def handle_event("save", %{"signup" => %{"email" => email}}, socket) do
    App.Signups.create!(%{name: socket.assigns.name, email: email})
    {:noreply, push_navigate(socket, to: "/done")}
  end
end
