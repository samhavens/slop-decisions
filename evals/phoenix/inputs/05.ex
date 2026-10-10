defmodule Example do
  use Phoenix.LiveView

  def mount(_params, _session, socket) do
    {:ok, assign(socket, :form, to_form(%{"name" => "", "email" => ""}, as: :profile))}
  end

  def render(assigns) do
    ~H"""
    <.form for={@form} id="profile" phx-change="validate" phx-submit="save">
      <input name="profile[name]" value={@form[:name].value} />
      <input name="profile[email]" value={@form[:email].value} />
      <button type="submit">Save</button>
    </.form>
    """
  end

  def handle_event("validate", %{"profile" => fields}, socket) do
    {:noreply, assign(socket, :form, to_form(fields, as: :profile))}
  end

  def handle_event("save", %{"profile" => fields}, socket) do
    App.Profiles.save!(fields)
    {:noreply, socket}
  end
end
