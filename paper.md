---
title: 'Neurosense: Automated Muscle Fasciculation Monitoring Using GMM-Based Foreground Segmentation'
tags:
  - muscle fasciculation
  - ultrasound
  - GMM
  - foreground segmentation
  - motor neuron disease

authors:
  - name: Dheeraj Pandey
    affiliation: 1
    orcid: 0009-0000-8395-9900
  - name: Adrian K. Davison
    affiliation: 1
    orcid: 0000-0002-6496-0209
affiliations:
  - name: Manchester Metropolitan University
    index: 1
date: 2025-07-07
bibliography: paper.bib
---


## Summary

The detection of moving regions in image sequences is a fundamental step in
many vision systems, including automated visual surveillance, human-machine
interface. We initially developed the system in MATLAB using Gaussian mixture
models for fasciculation detection (Bibbings, P. J. Harding, et al. 2019). 
Although effective, MATLAB has limitations in expanding and testing advanced 
methods. Python, with its rich set of machine learning and computer vision 
libraries, offers a better platform for future development.

We have successfully migrated our code to Python using OpenCV Back-
groundSubtractorMOG2 (Stauffer and Grimson 1999), which is also GMM-
based. With Python, NeuroSense can become a smarter and more accurate
tool, helping clinicians identify fasciculations earlier.

## Statement of need

Early detection is critical in conditions such as motor neuron disease (MND),
where timely intervention can significantly impact patient outcomes. The tran-
sition of Gaussian Mixture Model (GMM) implementation from MATLAB to
Python addresses the need for an open-source, scalable, and extensible platform
to support advanced statistical modeling and image analysis tasks.


```
Key Needs Driving the Transition:
```
- Scalability: With tools like OpenCV, sci-kit-learn, and distributed com-
    puting frameworks, Python provides a robust platform for handling large-
    scale datasets and computationally intensive tasks.
- Customization and Flexibility: The OpenCV GMM implementation al-
    lows for detailed customization of parameters and models, addressing
    domain-specific requirements beyond the constraints of the built-in func-
    tions of MATLAB.
- Community Support: Python’s global community fosters rapid develop-
    ment, shared resources, and continuous updates, ensuring long-term sus-
    tainability and innovation.

## Background

Motor neuron disease (MND) is characterized by progressive degeneration of
motor neurons leading to muscle weakness and wasting and reduced mobil-
ity, speech, swallowing, and respiratory abilities (Kiernan, Vucic, et al. 2011;
Bibbings, P. J. Harding, et al. 2019). These diseases are currently incurable
(Kiernan, Vucic, et al. 2011; Baumer, Talbot, et al. 2014; Bibbings, P. J. Hard-
ing, et al. 2019). To facilitate trials of new therapeutic interventions, there is a
significant need to identify sensitive markers of neuromuscular degeneration to
support early diagnosis and provide sensitive outcome measures of progression
(Kiernan, Vucic, et al. 2011). Ultrasound imaging provides a non-invasive (P.
Harding, Loram, et al. 2015), real-time view of larger muscle areas, making it
an alternative for fasciculation detection. We introduce a novel application of
adaptive foreground detection using Gaussian Mixture Models to identify fas-
ciculations in ultrasound image sequences. The tool was tested in five skeletal
muscles in healthy individuals and individuals affected by MND.

## The NeuroSense Tool

NeuroSense is an open-source software tool developed to objectively detect and
quantify muscle fasciculations in ultrasound video sequences. It uses an adap-
tive background subtraction method based on Gaussian Mixture Models (Kaew-
TraKulPong and Bowden 2002), allowing it to identify involuntary twitch events
that are often subtle and brief. The tool processes ultrasound videos by mod-
eling pixel-level motion over time, effectively distinguishing background motion
from muscle activity associated with fasciculations. It was designed to operate
on a range of skeletal muscles and to be resistant to variations in ultrasound
probe orientation, an important factor in clinical workflows.


```
Figure 1: High-level Architecture
```
We based our approach on the observation that fasciculations cause move-
ment across consecutive frames. To identify a meaningful duration for detect-
ing such twitches, we experimented with various frame-window sizes. In videos
captured at 80 frames per second (FPS), we found that a fasciculation typically
occurs within a 15-frame window. To generalise this approach for videos with
different frame rates, we implemented a proportional logic that scales the detec-
tion window based on the FPS. For instance, if a fasciculation spans 15 frames
at 80 FPS (approximately 187.5 milliseconds), we apply the same temporal win-
dow (in milliseconds) proportionally to other frame rates. This strategy ensures
consistent and reliable detection of fasciculations regardless of the FPS of the
video. Higher-magnitude twitches that persist longer, for example, across 30
frames, are still considered a single fasciculation, as they represent one continu-
ous event. This proportionally adjusted window has shown improved robustness
and accuracy in various cases.

The architecture diagram as shown in figure 1, illustrates the workflow of the
NeuroSense system, a web-based application for detecting fasciculations in clin-
ical ultrasound videos. Users upload single or multiple videos via a local server
or using tools like ngrok. They select the muscle group and probe orientation
before processing begins. The system extracts frames, applies background sub-
traction, and performs blob detection to identify fasciculations. The results
are served through a user interface that displays processed video, fasciculation
count, frame rate, and graphical visualisations. This pipeline enables clinicians 
to analyse muscle activity efficiently and consistently. It has been used in internal
Manchester Metropolitan University (MMU) research projects focusing on early ALS diagnostics, 
and aligns with methodologies used in wider scientific studies investigating neuromuscular
biomarkers.


## Acknowledgements

This work was supported by financial assistance through Manchester Metropoli-
tan University’s (MMU) scholarships in Life Sciences.


## References