<h1>Simple Video Carousel Generator</h1>
A Python-based tool for creating a carousel of videos (videos move one after another). The tool currently only supports right to left movement. 

The tool works using the concept of threshold and focus object. The focus object is the object that is the object that is prominent on the output video. A video becomes focused after its _Timecode In_ (see table below) time. A video that's in focus is the on that is playing, unfocused video will be frozen at its trimmed first frame. The threshold is the point on the output video that each clip should reach at its _Timecode Out_ time.

<h3>Usage</h3>

1. <b> Install Python and pip (if required) </b>
2. <b> Install dependency  </b>

&nbsp;`pip install opencv-python`
>&nbsp;&nbsp;Depending on Python installation, pip maybe be mapped to a different name for each version of Python. Run the following two commands and make sure that their version matches   
&nbsp;`pip -V`  
&nbsp;`python -V` 
> 
> &nbsp;&nbsp; If python or pip is not found, try `python<version>` e.g. `python3.7` for Python3.7
> 
>


3.<b> Put files in the right place  </b>
- Create a new folder
- In that folder paste the two python files
- Create a folder inside this folder named "source"
- Paste input videos into the source folder

4. <b> Creating a script file  </b>
&nbsp;Use sheets editor e.g. Google Sheets or Microsoft Excel to create an empty sheet. The format of the script file should be as follows.
   
Row | A | B | C | D | E | F | G | H | I | J |
--------- | ------- | ---------------- | ---------- | --------- | --------- | ---------| --------- | ---------| --------- | ---------:
1  | Output Width | Output Height | Output FPS | Spacing<sup>1</sup> | Threshold<sup>2</sup> | Minimum Ramp Speed<sup>3</sup> | Video Height<sup>4</sup>
2  | File Name | Timecode In<sup>5</sup> | Timecode Out | Trim Start | Trim End | FPS Override<sup>6</sup> | Top Crop<sup>7</sup> | Bottom Crop<sup>7</sup> | Left Crop<sup>8</sup> | Right Crop<sup>8</sup>
...   | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
Last  |  ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

> <b>Output Width: </b> Width of the output video in pixels  
> <b>Output Height:  </b> Height of the output video in pixels  
> <b>Output FPS: </b> Framerate of output video in frames per second  
> <b>Spacing: </b>Spacing between videos in pixels  
> <b>Threshold: </b>Spacing between the left edge of the video, and the threshold  
> <b>Minimum Ramp Speed: </b>Maximum rate of change of speed of the carousel in frames per second per second  
> <b>Video Height: </b>The height of the input video in pixels
> 
> <b>File Name: </b>Name of the source video file  
> <b>Timecode In: </b>The time that the video should become active (be playing) in seconds relative to start of the output video  
> <b>Timecode Out: </b>The time that the video's right edge should reach the threshold in seconds relative to start of the output video  
> <b>Trim Start: </b>How much of the input video's start should be trimmed in   
> <b>Trim End: </b>How much of the input video's end should be trimmed in seconds  
> <b>FPS Override: </b>Overrides the FPS detected in the media data. Enter 0 to use FPS in the media data. 
> <b>Top Crop, Bottom Crop: </b>Amount of cropping done to the top or bottom of input video, relative to its height  
> <b>Left Crop, Right Crop: </b>Amount of cropping done to the left or right of the input video, relative to its width
>

> <sup>1</sup>Spacing is overridden by default in renderer.py, <b>line 15</b>  
> Remove `script.relative_spacing(script.height, 0.05)` to use value provided in script.csv  
> _Default value sets spacing to be equal to 5% of the output video height_
> 
> <sup>2</sup>Threshold is overridden by default in renderer.py, <b>line 14</b>  
> `script = Script(script_raw, thresh_rel_width=0.47, height_rel__height=0.9, center_vertically=True)`  
> Remove `, thresh_rel_width=0.47` to use value provided in script.csv  
> _Default value sets threshold to be equal to 47% of the output video width_
> 
> <sup>3</sup>Minimum Ramp Speed is a suggestive value, the renderer may override this value if required  
> 
> <sup>4</sup>Video Height is overridden by default in renderer.py, <b>line 14</b>  
> Remove `, height_rel_height=0.9` to use value provided in script.csv  
> Optional: Replace `, center_vertically=True` with `, center_vertically=False` to keep the video at the top of the output video (y = 0)  
> Video Height should <b> never </b> exceed the output video height
> _Default value sets the height to be equal to 90% of the output video width_
> 
> <sup>5</sup>Timecode In should match the previous video's Timecode Out except for the first clip where the Timecode In can be set to any value (will affect the speed that the clip enters)  
> 
> <sup>6</sup>Should only be used when the media data is incorrectly read, an incorrect override can cause the video to be played at an incorrect speed.
> 
> <sup>7, 8</sup>The sum of the pair of values should <b> never </b> be more than or equal to 1
> 

5. <b> Run the code  </b>
Open command prompt (Windows) or Terminal (Mac). Run the following, replace _PATH_TO_FOLDER_ with the file path to the folder you created in Step 2  
   `python /PATH_TO_FOLDER/renderer.py`
   
> Again, ensure that you're running the same version of Python as the pip you used in step 2
> 
6. <b>Wait until rendering is complete</b>  
   A small window should open for you to preview the render as it happens in real-time. Output video will appear in the folder after the rendering finished. The output file will be named "export.avi". If the rendering takes to long, or you wish to cancel the render, press Control + C in the terminal/command prompt window.