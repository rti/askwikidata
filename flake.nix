{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python-packages = ps: with ps; [
        jupyterlab
        torch
        tqdm
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
        coverage

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
Run unit tests:
$ python -m unittest

Run unit tests with coverage report:
$ coverage run -m unittest
$ coverage report --omit="test_*,/nix/*" --show-missing
_EOF
        '';
      };
    };
}
