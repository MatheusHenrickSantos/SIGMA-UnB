defmodule PainelSigma.Repo do
  use Ecto.Repo,
    otp_app: :painel_sigma,
    adapter: Ecto.Adapters.Postgres
end
