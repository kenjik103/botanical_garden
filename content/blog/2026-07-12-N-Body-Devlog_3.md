Title: N-body devlog #3 - Kick, Drift, Kick
Date: 2026-07-11
Slug: n-body-devlog-3
Image: n-body/blog3header.png
Description: Why nothing in my life ever comes easy and integrating acceleration
Related: [[N-body]]

![hiya]({static}/images/n-body/blog3header.png){: .centered}

### Taking Stock

Thanks to our formula from blog post 1:
$$
a_{i} = G * \sum{\frac{m_j\mathbf{r_{ij}}}{(|\mathbf{r_{ij}}|^2+{\varepsilon^2}) ^{\frac{3}{2}}}}
$$
and code from [GPU Gems](https://developer.nvidia.com/gpugems/gpugems3/part-v-physics-simulation/chapter-31-fast-n-body-simulation-cuda), we have the following logic computing our acceleration:

```cpp
__device__ float3 body_interaction(float4 bi, float4 bj, float3 ai) {
   float3 r;
   r.x = bj.x - bi.x;
   r.y = bj.y - bi.y;
   r.z = bj.z - bi.z;
   
   float distSqr = r.x * r.x + r.y * r.y + r.z * r.z + EPS2;
   float distSixth = distSqr * distSqr * distSqr;
   float invDistCube = 1.0f/sqrtf(distSixth);
   float s = bj.w * invDistCube; //bj.w contains the mass of body j
   
   ai.x += r.x * s;
   ai.y += r.y * s;
   ai.z += r.z * s;
   return ai;
}

__global__ void accel_compute(const float4* d_p, float4* d_a) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < num_bodies) {
        float3 a_i = float3(0.f, 0.f, 0.f);
        for (int j = 0; j < num_bodies; j++) {
            if (i != j) {
                a_i = body_interaction(d_p[i], d_p[j], a_i);
            }
        }
        d_a[i] = float4(a_i.x, a_i.y, a_i.z, 0.f);
    }
}
```

Note the softening factor squared, `EPS2`, is set to `0.025` and mixed into the squared distance. `G` is set to 1 and omitted for simplicity's sake. Picking the right values for constants, and parameters more generally, is a problem worth its own blog post; I'll save it for another day.

![velocity]({static}/images/n-body/velocity.gif){: .centered}

### Velocity and Position

Obviously I can't move my bodies off of acceleration alone. Ultimately, I'll need to be updating positions per frame, so I'll need to integrate velocity and position. The classic way to do this is with Euler integration:

```c++
position += velocity * delta_t
velocity += acceleration * delta_t
```

Nice and straightforward. Almost too nice...

Alas, while Euler integration works for games and situations where acceleration is mostly constant, acceleration in the N-body sim is ever-changing; Euler can't keep up. When we sample force via our acceleration compute kernel, we *HAVE* to assume it remains constant over the entire $\Delta t$ time step, which it clearly isn't.

As a result, depending on whether we choose to integrate based off of the accelerations at the start or end of $\Delta t$ we get an inward or outward drift

![velocity]({static}/images/n-body/EulerDrift.png){: .centered}

If we compute acceleration based off the starting position of a body, we get an outward drift (Forward Euler). If we compute acceleration based off the ending position of a body, we get an inward drift (Backward Euler).
### The Fix

In a perfect world, the fix would be to take an average of Forward and Backward Euler. While we can't get an exact average, using the Leapfrog Kick-Drift-Kick method we can get close enough. The idea is, we stagger velocity and position integration such that position is computed off of a blend of velocities integrated at the beginning and end of each time step.

![velocity]({static}/images/n-body/Leapfrog.png){: .centered}

The result is the velocity "leapfrogging" over the position, hence the name.

In practice, this makes the integration of position closely match the shape of our ideal orbit. We slightly overshoot, then slightly undershoot, resulting in an overall trajectory that stays in orbit.

![velocity]({static}/images/n-body/KDK.png){: .centered}

Implementation wise, we do a half kick, drift, half kick, repeat.

```c++
__global__ void kick(const float4* d_a, float4* d_v, const float dt) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < num_bodies) {
        d_v[i] += 0.5 * d_a[i] * dt ;
    }
}

__global__ void drift(float4* d_p, const float4* d_v, const float dt) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < num_bodies) {
        d_p[i] += d_v[i] * dt ;
    }
}

int main(){
	accel_compute <<<num_blocks, num_threads, 0, hipStreamDefault>>>(d_p, d_a) ;
	for (;;) {
	    kick<<<num_blocks, num_threads, 0, hipStreamDefault>>>(d_a, d_v, dt);
	    drift<<<num_blocks, num_threads, 0, hipStreamDefault>>>(d_p, d_v, dt);
	    accel_compute <<<num_blocks, num_threads,
				         0, hipStreamDefault>>>(d_p, d_a);
	    kick<<<num_blocks, num_threads, 0, hipStreamDefault>>>(d_a, d_v, dt);
	}
}
```

Note that kick 1 is done based off of the old acceleration at the start of the step and kick 2 is done off the new acceleration at the end of each step.

### Wrapping up

Time for the big reveal — the fruits of our labor so far.

<video controls loop muted playsinline class="centered" style="max-width:100%">
  <source src="{static}/images/n-body/2body.webm" type="video/webm">
  Your browser doesn't support embedded video.
</video>

Amazing. 

It might look like a far cry from the complex thousand star systems I promised, but at this point the physics is done. The only thing standing between me and a galaxy is the initialization parameters; picking out the mass, positions, and velocities of the thousands of stars such that they orbit each other in a stable and visually appealing way.

Stay tuned!
