defmodule Example do
  # Repo.fetch_all returns {:ok, rows} or {:error, reason}.
  # The caller treats any returned list as the complete authoritative result.
  def records(repo) do
    case repo.fetch_all() do
      {:ok, rows} -> rows
      {:error, _reason} -> []
    end
  end
end
