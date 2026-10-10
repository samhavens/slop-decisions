defmodule Example do
  def cards do
    App.Feed.posts()
    |> Enum.map(&App.Feed.card/1)
  end
end
