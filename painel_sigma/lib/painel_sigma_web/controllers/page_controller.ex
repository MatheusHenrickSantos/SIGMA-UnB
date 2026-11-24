defmodule PainelSigmaWeb.PageController do
  use PainelSigmaWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end
