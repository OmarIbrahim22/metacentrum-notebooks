# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: MATLAB
#     language: matlab
#     name: matlab
# ---

# %% [markdown]
# # 07 - MATLAB Kernel Demonstration
#
# ## Goal
#
# Demonstrate using Jupyter with a MATLAB kernel. This notebook shows how to verify MATLAB availability, switch kernels, perform basic computations, create visualizations, and work with MATLAB-specific features in a Jupyter environment.
#
# **Runtime**: ~2-3 minutes (if MATLAB is available)
#
# **Note**: MATLAB requires a license and is typically only available on institutional platforms like MetaCentrum or through university access. This notebook will gracefully degrade if MATLAB is not available.

# %% [markdown]
# ## What You Will Learn
#
# - How to verify MATLAB kernel availability
# - How to switch to MATLAB kernel in Jupyter
# - How to perform basic MATLAB computations
# - How to work with matrices and arrays
# - How to create plots and visualizations
# - How to use MATLAB toolboxes (if available)
# - Platform-specific considerations for MATLAB in Jupyter

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - MATLAB installed with valid license
# - MATLAB kernel for Jupyter (matlab_kernel or jupyter-matlab-proxy)
# - Sufficient MATLAB license tokens available

# %% [markdown]
# ### Where to Get MATLAB Access
#
# **On MetaCentrum/e-INFRA CZ**:
# - MATLAB may be available via module system
# - Check: `module avail matlab`
# - Load: `module load matlab`
# - Access through OnDemand interface: https://ondemand.metacentrum.cz/
#
# **University/Institutional Access**:
# - Many universities provide MATLAB licenses
# - Check your institution's software portal
# - May require VPN or on-campus network
#
# **Local Installation**:
# - Requires MathWorks license (commercial or academic)
# - Install MATLAB first: https://www.mathworks.com/
# - Then install kernel: `pip install matlab_kernel`

# %% [markdown]
# ### MATLAB Kernel Installation
#
# **Option 1: matlab_kernel (Python-based)**
# ```bash
# pip install matlab_kernel
# python -m matlab_kernel install --user
# ```
#
# **Option 2: jupyter-matlab-proxy (MathWorks official)**
# ```bash
# pip install jupyter-matlab-proxy
# ```

# %% [markdown]
# ### How to Switch Kernels
#
# **In Jupyter Lab/Notebook**:
# 1. Kernel menu → Change Kernel → Select "MATLAB"
# 2. Or create new notebook and select MATLAB kernel
#
# **On MetaCentrum OnDemand**:
# 1. Launch Jupyter from OnDemand interface
# 2. Load MATLAB module first if required
# 3. Select MATLAB kernel when creating notebook

# %% [markdown]
# ### Required Environment Variables
#
# None - MATLAB uses its own licensing system.

# %% [markdown]
# ## Setup
#
# **Important**: Switch this notebook to the MATLAB kernel before running cells below!
#
# If you haven't switched yet:
# - **JupyterLab**: Kernel menu → Change Kernel → MATLAB
# - **Classic Notebook**: Kernel → Change kernel → MATLAB
# - **OnDemand**: Select MATLAB kernel when creating the notebook

# %% [markdown]
# ### 1. Verify MATLAB Environment

# %% vscode={"languageId": "matlab"}
% Print MATLAB version and system information
try
  disp('============================================================')
  disp('MATLAB Environment Check')
  disp('============================================================')
  disp(' ')

  % MATLAB version
  disp('MATLAB Version:')
  disp(version)

  % System information
  disp(' ')
  disp('System Information:')
  disp(['  Release: ', version('-release')])
  disp(['  Platform: ', computer])

  % License info (without revealing license number)
  disp(' ')
  disp('License check:')
  if license('test', 'MATLAB')
    disp('  ✓ MATLAB license valid')
  else
    disp('  ✗ MATLAB license issue')
  end

  % Toolboxes
  disp(' ')
  disp('Installed toolboxes:')
  tbx = ver;
  for i = 1:min(5, length(tbx))
    fprintf('  - %s\n', tbx(i).Name);
  end
  if length(tbx) > 5
    fprintf('  ... and %d more\n', length(tbx) - 5);
  end

  disp(' ')
  disp('✓ MATLAB kernel is working!')
catch err
  fprintf('✗ Error in MATLAB environment check: %s\n', err.message);
end

# %% [markdown]
# ## Minimal Working Demo
#
# ### 2. Basic MATLAB Operations

# %% vscode={"languageId": "matlab"}
try
  disp(' ')
  disp('============================================================')
  disp('Basic MATLAB Operations')
  disp('============================================================')
  disp(' ')

  % Scalar operations
  a = 10;
  b = 5;
  disp(['a = ', num2str(a)])
  disp(['b = ', num2str(b)])
  disp(['a + b = ', num2str(a + b)])
  disp(['a * b = ', num2str(a * b)])
  disp(['a ^ 2 = ', num2str(a ^ 2)])
  disp(['sqrt(a) = ', num2str(sqrt(a))])

  % Vector
  disp(' ')
  v = [1, 2, 3, 4, 5];
  disp('Vector v:')
  disp(v)
  disp(['Sum: ', num2str(sum(v))])
  disp(['Mean: ', num2str(mean(v))])
  disp(['Max: ', num2str(max(v))])
  disp(['Min: ', num2str(min(v))])

  disp(' ')
  disp('✓ Basic operations complete')
catch err
  fprintf('✗ Error in basic operations: %s\n', err.message);
end

# %% [markdown]
# ### 3. Matrix Operations

# %% vscode={"languageId": "matlab"}
try
  disp(' ')
  disp('============================================================')
  disp('Matrix Operations')
  disp('============================================================')
  disp(' ')

  % Create matrices
  A = [1, 2, 3; 4, 5, 6; 7, 8, 9];
  B = [9, 8, 7; 6, 5, 4; 3, 2, 1];

  disp('Matrix A:')
  disp(A)

  disp('Matrix B:')
  disp(B)

  % Matrix addition
  disp('A + B:')
  disp(A + B)

  % Element-wise multiplication
  disp('A .* B (element-wise):')
  disp(A .* B)

  % Matrix multiplication
  disp('A * B (matrix multiplication):')
  disp(A * B)

  % Transpose
  disp('Transpose of A:')
  disp(A')

  % Determinant (for square matrix)
  C = [1, 2; 3, 4];
  disp('Matrix C = [1 2; 3 4]')
  disp(['Determinant of C: ', num2str(det(C))])

  % Inverse
  disp('Inverse of C:')
  disp(inv(C))

  disp(' ')
  disp('✓ Matrix operations complete')
catch err
  fprintf('✗ Error in matrix operations: %s\n', err.message);
end

# %% [markdown]
# ### 4. Creating Visualizations

# %% vscode={"languageId": "matlab"}
try
  disp(' ')
  disp('============================================================')
  disp('Creating Visualizations')
  disp('============================================================')
  disp(' ')

  % Create data for plotting
  x = linspace(0, 2*pi, 100);
  y1 = sin(x);
  y2 = cos(x);

  % Create a figure with multiple subplots
  figure('Position', [100, 100, 800, 600]);

  % Plot 1: Line plot
  subplot(2, 2, 1)
  plot(x, y1, 'b-', 'LineWidth', 2)
  hold on
  plot(x, y2, 'r--', 'LineWidth', 2)
  grid on
  title('Sine and Cosine Functions')
  xlabel('x')
  ylabel('y')
  legend('sin(x)', 'cos(x)')

  % Plot 2: Scatter plot
  subplot(2, 2, 2)
  scatter(y1, y2, 50, x, 'filled')
  colorbar
  title('Parametric Plot')
  xlabel('sin(x)')
  ylabel('cos(x)')
  grid on

  % Plot 3: Bar chart
  subplot(2, 2, 3)
  data = [23, 45, 12, 67, 34];
  bar(data)
  title('Sample Bar Chart')
  xlabel('Category')
  ylabel('Value')
  grid on

  % Plot 4: 3D surface
  subplot(2, 2, 4)
  [X, Y] = meshgrid(-2:0.2:2, -2:0.2:2);
  Z = X .* exp(-X.^2 - Y.^2);
  surf(X, Y, Z)
  title('3D Surface')
  xlabel('X')
  ylabel('Y')
  zlabel('Z')
  colormap('jet')
  shading interp

  disp('✓ Plots created successfully!')
catch err
  fprintf('✗ Error creating visualizations: %s\n', err.message);
end

# %% [markdown]
# ### 5. Solving Linear System

# %% vscode={"languageId": "matlab"}
try
  disp(' ')
  disp('============================================================')
  disp('Solving Linear System')
  disp('============================================================')
  disp(' ')

  % Solve Ax = b
  A = [3, 2, -1; 2, -2, 4; -1, 0.5, -1];
  b = [1; -2; 0];

  disp('System: Ax = b')
  disp(' ')
  disp('Matrix A:')
  disp(A)
  disp('Vector b:')
  disp(b)

  % Solve using backslash operator
  x = A \ b;

  disp('Solution x:')
  disp(x)

  % Verify solution
  disp('Verification (A*x should equal b):')
  disp(A*x)

  % Check error
  residual = norm(A*x - b);
  disp(['Solution error (norm): ', num2str(residual)])

  disp(' ')
  disp('✓ Linear system solved successfully')
catch err
  fprintf('✗ Error solving linear system: %s\n', err.message);
end

# %% [markdown]
# ### 6. Statistical Analysis

# %% vscode={"languageId": "matlab"}
try
  disp(' ')
  disp('============================================================')
  disp('Statistical Analysis')
  disp('============================================================')
  disp(' ')

  % Generate random data
  rng(42);  % Set seed for reproducibility
  data = randn(1000, 1) * 10 + 50;  % Normal distribution, mean=50, std=10

  disp('Generated 1000 random samples from N(50, 10)')
  disp(' ')

  % Calculate statistics
  disp('Statistics:')
  disp(['  Mean:     ', num2str(mean(data))])
  disp(['  Median:   ', num2str(median(data))])
  disp(['  Std Dev:  ', num2str(std(data))])
  disp(['  Variance: ', num2str(var(data))])
  disp(['  Min:      ', num2str(min(data))])
  disp(['  Max:      ', num2str(max(data))])

  % Create histogram
  figure;
  histogram(data, 30, 'Normalization', 'pdf')
  hold on

  % Overlay theoretical normal distribution
  x_range = linspace(min(data), max(data), 100);
  y_theory = normpdf(x_range, 50, 10);
  plot(x_range, y_theory, 'r-', 'LineWidth', 2)

  title('Data Distribution vs Theoretical Normal')
  xlabel('Value')
  ylabel('Probability Density')
  legend('Sample Data', 'N(50, 10)')
  grid on

  disp(' ')
  disp('✓ Statistical analysis complete')
catch err
  fprintf('✗ Error in statistical analysis: %s\n', err.message);
end

# %% [markdown]
# ### 7. Numerical Integration

# %% vscode={"languageId": "matlab"}
try
  disp(' ')
  disp('============================================================')
  disp('Numerical Integration')
  disp('============================================================')
  disp(' ')

  % Define function to integrate
  f = @(x) x.^2 .* sin(x);

  disp('Integrating f(x) = x^2 * sin(x) from 0 to pi')
  disp(' ')

  % Numerical integration using integral()
  result = integral(f, 0, pi);

  disp(['Numerical result: ', num2str(result)])

  % Plot the function
  x = linspace(0, pi, 100);
  y = f(x);

  figure;
  plot(x, y, 'b-', 'LineWidth', 2)
  hold on
  area(x, y, 'FaceAlpha', 0.3)
  grid on
  title('Function to Integrate: f(x) = x^2 sin(x)')
  xlabel('x')
  ylabel('f(x)')
  legend('f(x)', 'Area under curve')

  disp(' ')
  disp('✓ Numerical integration complete')
catch err
  fprintf('✗ Error in numerical integration: %s\n', err.message);
end

# %% [markdown]
# ### 8. Simple Symbolic Math (if Symbolic Toolbox available)

# %% vscode={"languageId": "matlab"}
try
  disp(' ')
  disp('============================================================')
  disp('Symbolic Math Demo')
  disp('============================================================')
  disp(' ')

  % Check if Symbolic Math Toolbox is available
  if license('test', 'Symbolic_Toolbox')
    disp('✓ Symbolic Math Toolbox available')
    disp(' ')

    try
      % Define symbolic variable
      syms x

      % Define function
      f = x^3 - 3*x^2 + 2*x;
      disp('Function: f(x) = x^3 - 3x^2 + 2x')

      % Derivative
      df = diff(f);
      disp(' ')
      disp('First derivative:')
      disp(df)

      % Integral
      F = int(f);
      disp(' ')
      disp('Indefinite integral:')
      disp(F)

      % Solve equation
      roots_f = solve(f == 0, x);
      disp(' ')
      disp('Roots of f(x) = 0:')
      disp(roots_f)
    catch sym_err
      fprintf('✗ Error in symbolic operations: %s\n', sym_err.message);
    end
  else
    disp('✗ Symbolic Math Toolbox not available')
    disp('  This is optional - core MATLAB works without it')
  end

  disp(' ')
  disp('✓ Symbolic math demo complete')
catch err
  fprintf('✗ Error in symbolic math demo: %s\n', err.message);
end

# %% [markdown]
# ## Cleanup
#
# Clean up workspace and close figures:

# %% vscode={"languageId": "matlab"}
disp(' ')
disp('============================================================')
disp('Cleanup')
disp('============================================================')
disp(' ')

% Close all figures
close all
disp('✓ All figures closed')

% Clear workspace (optional - uncomment if desired)
% clear all
% disp('✓ Workspace cleared')

disp(' ')
disp('Cleanup complete!')
disp('Note: Workspace variables are preserved unless explicitly cleared')

# %% [markdown]
# ## Troubleshooting
#
# ### Kernel Issues
#
# **MATLAB kernel not available**
# - MATLAB not installed or not in PATH
# - MATLAB kernel not installed: `pip install matlab_kernel`
# - Kernel not registered: `python -m matlab_kernel install --user`
# - Check: `jupyter kernelspec list`
#
# **"MATLAB executable not found" error**
# - MATLAB not in system PATH
# - On Linux: Add MATLAB to PATH or create symlink
# - On MetaCentrum: Load MATLAB module first: `module load matlab`
#
# **Kernel crashes or won't start**
# - License issues (see below)
# - MATLAB version incompatibility
# - Check Jupyter logs for details
# - Try restarting Jupyter server

# %% [markdown]
# ### License Issues
#
# **"License checkout failed"**
# - No MATLAB licenses available
# - On shared systems, licenses may be in use
# - Wait and retry, or contact admin
# - Check license server status
#
# **"Cannot connect to license server"**
# - Network connectivity to license server
# - VPN required?
# - Firewall blocking license port (typically 27000-27009)
# - Check MATLAB license configuration
#
# **License expires during session**
# - Long-running notebooks may lose license
# - MATLAB checks out license on start
# - Save work and restart kernel if needed

# %% [markdown]
# ### Platform-Specific Issues
#
# **MetaCentrum/OnDemand**
# - Use OnDemand interface for easiest MATLAB access
# - Pre-configured with license and kernel
# - If using PBS: Request sufficient walltime for license
# - Load MATLAB module in PBS script before starting Jupyter
#
# **JupyterHub**
# - MATLAB may need to be in shared environment
# - Check with administrator for license configuration
# - May require special kernel installation by admin
#
# **Local installation**
# - Ensure MATLAB is properly licensed
# - matlab_kernel needs to find MATLAB executable
# - On Windows: Usually works automatically
# - On Linux/Mac: May need PATH configuration

# %% [markdown]
# ### Toolbox Issues
#
# **"Undefined function or variable"**
# - Function requires specific toolbox
# - Check if toolbox installed: `ver`
# - Check if toolbox licensed: `license('test', 'Toolbox_Name')`
# - Contact admin if toolbox needed
#
# **Toolbox license not available**
# - Similar to main license issues
# - Toolboxes have separate license counts
# - Use base MATLAB functions when possible

# %% [markdown]
# ### Performance Issues
#
# **Slow execution**
# - MATLAB startup overhead in each cell
# - Large data in workspace
# - Inefficient code (use vectorization)
# - Profile code: `profile on; ... ; profile viewer`
#
# **Memory issues**
# - MATLAB loads all data in memory
# - Clear large variables: `clear large_var`
# - Use `whos` to see memory usage
# - Request more RAM in job allocation

# %% [markdown]
# ### Plotting Issues
#
# **Figures don't appear**
# - May need to explicitly display: `figure; plot(...)`
# - Check MATLAB graphics system
# - Try: `set(0, 'DefaultFigureVisible', 'on')`
#
# **Poor plot quality**
# - Adjust figure size: `figure('Position', [x, y, width, height])`
# - Increase resolution for export
# - Use vector formats for publication

# %% [markdown]
# ### Debugging Tips
#
# ```matlab
# % Check MATLAB version
# version
#
# % Check license
# license
#
# % List toolboxes
# ver
#
# % Check workspace
# whos
#
# % Get help
# help plot
# doc plot
#
# % Find functions
# lookfor 'keyword'
#
# % Debug mode
# dbstop if error  % Break on error
# dbclear all      % Clear breakpoints
# ```

# %% [markdown]
# ## Next Steps
#
# Now that you understand MATLAB in Jupyter, you can:
#
# ### Advanced MATLAB Features
#
# - **Simulink** - Model-based design and simulation
# - **App Designer** - Create interactive applications
# - **Parallel Computing** - Use multiple cores or GPUs
# - **Code Generation** - Generate C/C++ code from MATLAB
# - **Live Editor** - Alternative to Jupyter (MATLAB native)

# %% [markdown]
# ### Common Toolboxes
#
# - **Signal Processing** - Filter design, spectral analysis
# - **Image Processing** - Computer vision, image analysis
# - **Statistics & ML** - Classification, regression, clustering
# - **Optimization** - Linear, nonlinear, integer programming
# - **Control System** - Control design and analysis
# - **Deep Learning** - Neural networks, transfer learning

# %% [markdown]
# ### Integration with Other Languages
#
# **MATLAB ↔ Python**:
# - Call Python from MATLAB: `py.module.function()`
# - Call MATLAB from Python: MATLAB Engine API
# - Share data structures between languages
#
# **MATLAB ↔ C/C++**:
# - MEX files for performance-critical code
# - Call C libraries from MATLAB
# - Generate C code from MATLAB

# %% [markdown]
# ### Workflow Integration
#
# **Multi-kernel notebooks**:
# 1. Use Python for data acquisition
# 2. Switch to MATLAB for specific analysis
# 3. Switch to R for statistical tests
# 4. Back to Python for deployment
#
# **File-based workflow**:
# - MATLAB saves data: `save('data.mat', 'variable')`
# - Python loads with scipy: `scipy.io.loadmat('data.mat')`
# - Or use CSV/HDF5 for language-agnostic formats

# %% [markdown]
# ### Best Practices
#
# **Code organization**:
# - Use functions for reusable code
# - Add comments and help text
# - Follow MATLAB style guidelines
# - Use meaningful variable names
#
# **Performance**:
# - Vectorize instead of loops
# - Pre-allocate arrays
# - Use appropriate data types
# - Profile before optimizing
#
# **Reproducibility**:
# - Set random seed: `rng(seed)`
# - Document MATLAB version: `version`
# - List toolboxes: `ver`
# - Save complete workspace if needed

# %% [markdown]
# ### When to Use MATLAB vs Alternatives
#
# **Use MATLAB when**:
# - Working with Simulink models
# - Using specialized toolboxes
# - Team already uses MATLAB
# - Industry-standard in your field
#
# **Consider alternatives when**:
# - Need open-source solution (Python/R)
# - License costs prohibitive
# - Deploying to production (licensing)
# - Need better package ecosystem

# %% [markdown]
# ### MetaCentrum-Specific Tips
#
# - Use OnDemand for interactive MATLAB work
# - For batch jobs, use compiled MATLAB or Octave
# - Monitor license usage on shared system
# - Save results frequently (walltime limits)
# - Use scratch storage for large temporary files

# %% [markdown]
# ### Related Notebooks
#
# - **06_r_kernel_demo.ipynb** - Another alternate kernel
# - **00_environment_check.ipynb** - Environment detection
# - **05_gpu_container_ai_model.ipynb** - MATLAB supports GPU too

# %% [markdown]
# ### Documentation
#
# - [MATLAB Documentation](https://www.mathworks.com/help/matlab/)
# - [matlab_kernel](https://github.com/Calysto/matlab_kernel)
# - [Jupyter MATLAB Proxy](https://github.com/mathworks/jupyter-matlab-proxy)
# - [MATLAB on MetaCentrum](https://wiki.metacentrum.cz/wiki/MATLAB)
# - [MATLAB Training](https://www.mathworks.com/services/training.html)
# - [MATLAB Central](https://www.mathworks.com/matlabcentral/)
