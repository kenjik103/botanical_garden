Title: N-body devlog #1
Date: 2026-06-04 13:25
Slug: n-body-devlog-1
Image: n-body/blog1header.jpg
Description: The motivation, the physics, and why thousands of gravitating bodies fit the GPU programming model perfectly.

![freshmen computer scientists developing a similar n-body simulator]({static}/images/n-body/blog1header.jpg){: .centered}

### Motivation
I've been abusing claude code quite a bit recently, so I figured I'd put on the nerd glasses and see if my brain still works. I go back to work in a month where I'll get a chance to lay down some CUDA kernels; I figured I'd better do some parallel programming to get the reps in, and the N-body problem is a good exercise for that.

### The N-body problem
The N-body problem is a physics problem that models how a bunch of celestial objects' (N of them) gravities interact with one another. The moon spinning around earth is a 2-body problem. The moon spinning around the earth spinning around the sun is a 3-body problem. What I'm shooting for is a humble 1000+ bodies, simulated via compute shader and rendered out via OpenGL. As you can imagine, doing this CPU side is unrealistic; every body needs to calculate the force applied to it by every other body. So for $n$ bodies thats $n^2$ computations per update. Thankfully, I have my wonderful Radeon™ RX 9070 XT AMD graphics card, which has been begging me to use it for anything other than Counterstrike.

![some pretty examples of the 3-body problem]({static}/images/n-body/3-body.resized.gif){: .centered}

### The Math
The math itself is pretty straightforward. The force body $j$ exerts on body $i$ can be represented by:
$$
f_{ij} = G{\frac{m_im_j}{|\mathbf{r_{ij}}|^3}}\mathbf{r_{ij}}
$$
which I know looks a little rough at first, but $m$ is mass (which I get to define for each body), and $\mathbf{r_{ij}}$ is the vector distance between the positions of $i$ and $j$; so at the end of the day, its just simple multiplication and division. $G$ is the gravitational constant $6.6743 × 10^{-11} m^3 kg^{-1} s^{-2}$ which I remember thinking was bullshit the first time I saw it in AP physics, but it is just a number at the end of the day.

Since this formula represents the force that **one** body applies on **one** other body, the total force exerted on **one** body by **all bodies** is 
$$F_{i} = \sum_{\substack{1 \le j \le N \\ j \neq i}} f_{ij}$$
which is just addition. Note that $f = ma$, and we ultimately want to solve for acceleration. Execute $F_i / m_i$ for every planet in your system, and you have one frame of your simulation. Nice!

But wait! A problem! Those of you with sharp eyes may have noticed that as two planets get close to one another, $|r_{ij}|^3$ quickly becomes microscopic. This spikes $f_{ij}$ and blows up our simulation, which is not ideal. To remedy this, we add a softening factor to the denominator; the exact details of which I'll go over later.

All of this is coming from [NVIDIA Gpu Gems Chapter 31](https://developer.nvidia.com/gpugems/gpugems3/part-v-physics-simulation/chapter-31-fast-n-body-simulation-cuda) by the way, so if you want to follow along or check my work, there you go.

![realistic planets]({static}/images/n-body/Confessio.jpg){: .centered}
### Conclusion
Simple operations executed across thousands of points fits the GPU programming model perfectly, and the visual of having thousands of stars swirling around is definitely enough to keep my monkey brain engaged, so I have high hopes for this project. Onward!
