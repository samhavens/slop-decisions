defmodule Example do
  use Phoenix.LiveView
  alias App.{Document, Repo}

  def mount(_params, %{"user_id" => user_id}, socket) do
    {:ok, assign(socket, user_id: user_id, document: nil)}
  end

  def render(assigns) do
    ~H"""
    <button phx-click="preview" phx-value-id="42">Preview document</button>
    <section :if={@document} id="preview"><p>{@document.body}</p></section>
    """
  end

  def handle_event("preview", %{"id" => id}, socket) do
    document = Repo.get_by!(Document, id: id, owner_id: socket.assigns.user_id)
    {:noreply, assign(socket, :document, document)}
  end
end
