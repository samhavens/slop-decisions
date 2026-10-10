defmodule App.Post do
  use Ecto.Schema
  schema "posts" do
    field :title, :string
    belongs_to :author, App.Author
  end
end

defmodule Example do
  import Ecto.Query
  alias App.{Post, Repo}

  def cards do
    Repo.all(from p in Post, order_by: p.id)
    |> Repo.preload(:author)
    |> Enum.map(&card/1)
  end

  defp card(post) do
    post = Repo.preload(post, :author)
    %{title: post.title, author: post.author.name}
  end
end
