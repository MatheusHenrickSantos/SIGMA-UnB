defmodule PainelSigma.Repo.Migrations.CriarTabelasLotus do
  use Ecto.Migration

  def up, do: Lotus.Migrations.up()
  def down, do: Lotus.Migrations.down()
end
