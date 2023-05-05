import launch

if not launch.is_installed("opencv-python"):
    launch.run_pip("install opencv-python", "opencv-python")

for dep in ['onnxruntime', 'pymatting', 'pooch', 'opencv-python']: # List dependancies here
    if not launch.is_installed(dep):
        launch.run_pip(f"install {dep}", f"{dep} for pixel extension")