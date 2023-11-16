{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python-packages = ps: with ps; [
        torch
        matplotlib
        langchain
        sentence-transformers
        transformers
        tokenizers
        tiktoken
        pandas
        psycopg
        annoy
        openai

        black
        ipython

        (
          buildPythonPackage rec {
            pname = "mentat";
            version = "1.0.2";
            src = fetchPypi {
              inherit pname version;
              sha256 = "sha256-r+rWxTLL4g1qJjfep9Uf4zdzZ4ISenonNq4k9P/tPvk=";
            };
            doCheck = false;
            propagatedBuildInputs = [
              # Specify dependencies
              pkgs.python3Packages.backoff
              pkgs.python3Packages.termcolor
              pkgs.python3Packages.sentry-sdk
              pkgs.python3Packages.python-dotenv
            ];
          }
        )
      ];
    in
    {
      devShell.${system} = pkgs.mkShell {
        buildInputs = with pkgs; with pkgs.python310Packages; [

          (pkgs.python3.withPackages python-packages)

          pyright

          (writeShellScriptBin "ipython-simple-prompt" ''
            ipython --simple-prompt --nosep "$@"
          '')

          # (writeShellScriptBin "wb" ''
          #   docker run --rm -it maxlath/wikibase-cli "$@"
          # '')
        ];

        shellHook = ''
          ${pkgs.figlet}/bin/figlet "askwikidata"

          cat << _EOF
$ docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password -d ankane/pgvector:v0.5.1
$ docker exec -it postgres psql -U postgres
$ docker exec -it postgres createdb -U postgres askwikidata

_EOF
        '';
      };
    };
}
