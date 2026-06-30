Title: N-body devlog #2 - HIP HIP Hooray
Date: 2026-06-04 06-30-2026
Slug: n-body-devlog-2
Image: n-body/blog2header.jpg
Description: Switching frameworks from OpenGL to ROCm HIP
Related: [[N-body]]

![Me realizing I had to write another shader]({static}/images/n-body/blog2header.jpg){: .centered}

### Frustration

You don't truly appreciate the convenient things in life until you go without them for a time. Live in the wilderness for a while, and you'll see your AC, grocery store, shower, laundry machine, etc in a new light. Spend a week writing shaders in OpenGL and you'll find yourself marveling at the simplicity of NVDIA CUDA. Such was the experience of a young, bright eyed developer (me) who foolishly believed all GPU programming languages were created equal.

In my defense, I did actually get the acceleration calculation loop working. That being said, the experience was so frusturating that when I realized I needed to write another kernel to integrate position and velocity I almost cried. In order to properly convey just how painful of an experience this was lets do a side-by-side comparison on what getting the acceleration loop set up looks like in OpenGL vs a traditional GPU programming language. I have an AMD graphics card, so we will be using AMD's ROCm HIP instead of CUDA. That said, HIP and CUDA are very similar; effectively identical for something this scale. Consider this a HIP appreciation post.
### Initializing GPU Buffers

In order for the CPU and GPU to communicate, a system of buffer sharing must be implemented. Lets look at how OpenGL implements this vs HIP. 
#### OpenGL
```c++
    GLuint  pos_ssbo{};
    glGenBuffers(1, &pos_ssbo);
    GLuint acc_ssbo{};
    glGenBuffers(1, &acc_ssbo);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, pos_ssbo);
    glBufferData(GL_SHADER_STORAGE_BUFFER,
        sizeof(body_positions), &body_positions, GL_DYNAMIC_COPY);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, pos_ssbo);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, acc_ssbo);
    glBufferData(GL_SHADER_STORAGE_BUFFER,
        sizeof(body_accelerations), &body_accelerations, GL_DYNAMIC_COPY);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, acc_ssbo);

```
#### ROCm HIP
```c++
	float4* d_p {};
    float4* d_a {};
    const size_t bytes = num_bodies * sizeof(float4);
    hipMalloc(&d_p, bytes);
    hipMalloc(&d_a, bytes);
    hipMemcpy(d_p, positions.data(), bytes, hipMemcpyHostToDevice);
    hipMemcpy(d_a, accelerations.data(), bytes, hipMemcpyHostToDevice);

```

Take a moment to appreciate the simple and logical workflow HIP achieved. Instantiate your buffer, malloc the appropriate size, and copy over your data. Done.

Now let me attempt to explain what is going on in the OpenGL side. I wrote this code myself and I'm still not 100% sure what's happening but nevertheless: Declare an ID for the buffer. Generate a generic buffer tied to the declared ID. Bind the generic buffer (by ID) to a specific buffer type the GPU can interface with. Copy the CPU data to the GPU buffer (by buffer type). Bind the buffer ID to a arbitrary "slot" ID within the GPU. Repeat.
###  Invoking the Kernel
#### OpenGL
```c++
		computeProgram.use();
        glDispatchCompute((BODY_COUNT + 255) / 256, 1, 1);
	    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT |
					    GL_VERTEX_ATTRIB_ARRAY_BARRIER_BIT);
```
#### ROCm HIP
```c++
        accel_compute <<<num_blocks,
				         num_threads,
				         0, hipStreamDefault>>>(d_p, d_a);
```

In OpenGL, the compute shader is a seperate file that needs to be compiled by yours truly. Because of this, a `ComputeShader` class was necessary to hide the file streaming and compiling logic. On top of this, lets compare the information we can glean off of the kernel invocations. On the ROCm HIP side, we have everything we need to know. The number of blocks, number of threads per block, the name of the kernel, and buffer dependencies are all there. On the OpenGL side, all we can see is the number of blocks. The rest of the information is scattered throughout the file, or in some cases, in an entirely separate file.

###  Defining the Kernel

#### OpenGL
```c++
#version 460 core

layout(std430, binding = 0) buffer Positions    {   vec4 positions[];  };
layout(std430, binding = 1) buffer  Accelerations   {   vec4 accelerations[];  };

layout(local_size_x = 256, local_size_y = 1, local_size_z = 1) in;

void main() {
...
}

```

#### ROCm HIP
```c++
__global__ void accel_compute(const float4* d_p, float4* d_a) {
...
}
```

Remember that buffer slot ID from earlier? I hope so because you're going to need it here. Also, I know the number of blocks was declared when you invoked the shader, but the number of threads within each block is going to need to be declared within the shader itself; that's just how thing are. Sorry.

Mind you, the compute shader itself is in an entirely different file from wherever you invoked it from. HIP kernels are declared like regular C++ functions; same file.

### Parting Thoughts

All of this is to say that the n-body project will be done in ROCm HIP rather than GLSL. At the end of the day, all I really care about with this project is the math and the GPU programming principles. I feel that wrangling with OpenGL is conducive to neither of these, so why bother.
