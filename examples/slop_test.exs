defmodule SlopDecisionsTest do
  use ExUnit.Case, async: false

  @moduletag slop: true, timeout: 300_000

  test "changed Elixir files pass the code checks" do
    executable = System.find_executable("slop-decisions") || flunk("Install slop-decisions first")
    base = System.get_env("SLOP_BASE", "HEAD")

    options =
      for {flag, variable} <- [
            {"--provider", "SLOP_PROVIDER"},
            {"--model", "SLOP_MODEL"},
            {"--base-url", "SLOP_BASE_URL"}
          ],
          value = System.get_env(variable),
          value != nil,
          argument <- [flag, value],
          do: argument

    {output, status} =
      System.cmd(
        executable,
        ["check", "--changed", base, "--format", "json"] ++ options,
        stderr_to_stdout: true
      )

    assert status == 0, output
  end
end
