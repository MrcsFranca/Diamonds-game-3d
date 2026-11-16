{pkgs ? import <nixpkgs> {}}: let
  pythonEnv = pkgs.python3.withPackages (ps:
    with ps; [
      pyopengl
      pillow
    ]);

  glLibraries = with pkgs; [
    freeglut
    libGLU
    libglvnd
  ];
in
  pkgs.mkShell {
    packages = [pythonEnv] ++ glLibraries;

    LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath glLibraries}:/run/opengl-driver/lib";
  }
