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
#     display_name: R
#     language: R
#     name: ir
# ---

# %% [markdown]
# # 06 - R Kernel Demonstration
#
# ## Goal
#
# Demonstrate using Jupyter with an R kernel instead of Python. This notebook shows how to switch kernels, work with R packages, perform basic data analysis, and create visualizations using R.
#
# **Runtime**: ~2-3 minutes
#
# **Note**: This notebook requires the R kernel (IRkernel) to be installed. On MetaCentrum/e-INFRA, this may already be available.

# %% [markdown]
# ## What You Will Learn
#
# - How to verify R kernel availability
# - How to switch between Python and R kernels
# - How to work with base R functionality
# - How to install R packages in user space
# - How to perform basic data analysis in R
# - How to create plots and visualizations
# - How to use R for statistical computing

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - R installed (usually available on MetaCentrum/e-INFRA)
# - IRkernel (Jupyter R kernel) installed
# - Ability to install R packages (in user library)

# %% [markdown]
# ### Where to Get R Kernel
#
# **On MetaCentrum/e-INFRA**: Often pre-installed
# - Check available kernels in Jupyter interface
# - Or load module: `module load R`
#
# **Local installation**:
# ```bash
# # Install R (system package manager)
# # Arch Linux:
# sudo pacman -S r
#
# # Install IRkernel (from R console):
# R
# > install.packages('IRkernel')
# > IRkernel::installspec(user = TRUE)
# ```

# %% [markdown]
# ### How to Switch Kernels
#
# **In Jupyter Lab/Notebook**:
# 1. Click "Kernel" menu → "Change Kernel" → Select "R"
# 2. Or create new notebook and select R kernel when prompted
#
# **In this demo**:
# - This notebook is designed to run with R kernel
# - If you see an error about "R_HOME", the R kernel is not available

# %% [markdown]
# ### Required Environment Variables
#
# None - this notebook works without credentials.

# %% [markdown]
# ## Setup
#
# **Important**: Switch this notebook to the R kernel before running cells below!
#
# If you haven't switched yet:
# - **JupyterLab**: Kernel menu → Change Kernel → R
# - **Classic Notebook**: Kernel → Change kernel → R

# %% [markdown]
# ### 1. Verify R Environment

# %% vscode={"languageId": "r"}
# Print R version and system information
tryCatch({
  cat(strrep("=", 61), "\n")
  cat("R Environment Check\n")
  cat(strrep("=", 61), "\n\n")

  cat("R Version:\n")
  print(R.version.string)

  cat("\nPlatform:\n")
  print(R.version$platform)

  cat("\nR Home Directory:\n")
  print(R.home())

  cat("\nUser Library Path:\n")
  print(.libPaths())

  cat("\n✓ R kernel is working!\n")
}, error = function(e) {
  cat("✗ Error in R environment check:", conditionMessage(e), "\n")
})

# %% [markdown]
# ### 2. Check Available Packages

# %% vscode={"languageId": "r"}
# List some commonly used packages
tryCatch({
  cat("\nChecking for common R packages:\n\n")

  packages_to_check <- c("base", "stats", "graphics", "ggplot2", "dplyr", "tidyr")

  for (pkg in packages_to_check) {
    result <- tryCatch(
      require(pkg, character.only = TRUE, quietly = TRUE),
      error = function(e) FALSE
    )
    if (result) {
      cat(sprintf("  ✓ %-15s installed\n", pkg))
    } else {
      cat(sprintf("  ✗ %-15s NOT installed\n", pkg))
    }
  }

  cat("\nNote: base, stats, graphics come with R by default\n")
}, error = function(e) {
  cat("✗ Error checking packages:", conditionMessage(e), "\n")
})

# %% [markdown]
# ## Minimal Working Demo
#
# ### 3. Basic R Operations

# %% vscode={"languageId": "r"}
tryCatch({
  cat(paste0("\n", strrep("=", 60)), "\n")
  cat("Basic R Operations\n")
  cat(strrep("=", 61), "\n\n")

  # Create a vector
  numbers <- c(1, 2, 3, 4, 5, 10, 15, 20)
  cat("Vector: ", numbers, "\n")

  # Basic statistics
  cat("\nBasic Statistics:\n")
  cat("  Mean:   ", mean(numbers), "\n")
  cat("  Median: ", median(numbers), "\n")
  cat("  SD:     ", sd(numbers), "\n")
  cat("  Min:    ", min(numbers), "\n")
  cat("  Max:    ", max(numbers), "\n")
  cat("  Sum:    ", sum(numbers), "\n")

  # Summary function
  cat("\nSummary:\n")
  print(summary(numbers))
}, error = function(e) {
  cat("✗ Error in basic R operations:", conditionMessage(e), "\n")
})

# %% [markdown]
# ### 4. Create and Analyze a Data Frame

# %% vscode={"languageId": "r"}
tryCatch({
  cat(paste0("\n", strrep("=", 60)), "\n")
  cat("Data Frame Analysis\n")
  cat(strrep("=", 61), "\n\n")

  # Create a sample data frame
  df <- data.frame(
    name = c("Alice", "Bob", "Charlie", "David", "Eve"),
    age = c(25, 30, 35, 28, 32),
    score = c(85, 92, 78, 88, 95),
    pass = c(TRUE, TRUE, TRUE, TRUE, TRUE)
  )

  cat("Sample Data Frame:\n")
  print(df)

  cat("\nData Frame Structure:\n")
  str(df)

  cat("\nData Frame Summary:\n")
  print(summary(df))

  cat("\nColumn Statistics:\n")
  cat("  Average age:   ", mean(df$age), "\n")
  cat("  Average score: ", mean(df$score), "\n")
  cat("  Pass rate:     ", sum(df$pass) / nrow(df) * 100, "%\n")
}, error = function(e) {
  cat("✗ Error in data frame analysis:", conditionMessage(e), "\n")
})

# %% [markdown]
# ### 5. Data Manipulation

# %% vscode={"languageId": "r"}
tryCatch({
  cat(paste0("\n", strrep("=", 60)), "\n")
  cat("Data Manipulation\n")
  cat(strrep("=", 61), "\n\n")

  # Guard: check that df and expected columns exist
  if (!exists("df")) stop("'df' not found — run the Data Frame cell first")
  if (!"score" %in% colnames(df)) stop("column 'score' not found in df")
  if (!"age" %in% colnames(df)) stop("column 'age' not found in df")

  # Filter data
  high_scorers <- df[df$score > 85, ]
  cat("Students with score > 85:\n")
  print(high_scorers)

  # Add a new column
  df$grade <- ifelse(df$score >= 90, "A",
                     ifelse(df$score >= 80, "B",
                            ifelse(df$score >= 70, "C", "D")))

  cat("\nData with grades:\n")
  print(df)

  # Sort by score
  df_sorted <- df[order(-df$score), ]
  cat("\nSorted by score (descending):\n")
  print(df_sorted)
}, error = function(e) {
  cat("✗ Error in data manipulation:", conditionMessage(e), "\n")
})

# %% [markdown]
# ### 6. Simple Visualization (Base R Graphics)

# %% vscode={"languageId": "r"}
tryCatch({
  cat(paste0("\n", strrep("=", 60)), "\n")
  cat("Creating Visualizations\n")
  cat(strrep("=", 61), "\n\n")

  if (!exists("df")) stop("'df' not found — run the Data Frame cell first")
  if (!"age" %in% colnames(df)) stop("column 'age' not found in df")
  if (!"score" %in% colnames(df)) stop("column 'score' not found in df")
  if (!"name" %in% colnames(df)) stop("column 'name' not found in df")

  # Set up plotting area for multiple plots
  par(mfrow=c(2, 2))

  # Plot 1: Scatter plot
  plot(df$age, df$score,
       main="Age vs Score",
       xlab="Age", ylab="Score",
       pch=19, col="blue")

  # Plot 2: Bar plot
  barplot(df$score, names.arg=df$name,
          main="Scores by Student",
          xlab="Student", ylab="Score",
          col="lightblue")

  # Plot 3: Histogram
  hist(df$age,
       main="Age Distribution",
       xlab="Age",
       col="lightgreen",
       breaks=5)

  # Plot 4: Box plot
  boxplot(df$score,
          main="Score Box Plot",
          ylab="Score",
          col="lightyellow")

  # Reset plotting area
  par(mfrow=c(1, 1))

  cat("✓ Plots created successfully!\n")
}, error = function(e) {
  par(mfrow=c(1, 1))  # always reset plot layout
  cat("✗ Error in visualization:", conditionMessage(e), "\n")
})

# %% [markdown]
# ### 7. Statistical Analysis

# %% vscode={"languageId": "r"}
tryCatch({
  cat(paste0("\n", strrep("=", 60)), "\n")
  cat("Statistical Analysis\n")
  cat(strrep("=", 61), "\n\n")

  # Generate sample data for analysis
  set.seed(42)  # For reproducibility
  x <- rnorm(100, mean=50, sd=10)
  y <- 2 * x + rnorm(100, mean=0, sd=5)

  # Correlation
  cat("Correlation between x and y:\n")
  cor_result <- cor.test(x, y)
  print(cor_result)

  # Linear regression
  cat("\nLinear Regression (y ~ x):\n")
  model <- lm(y ~ x)
  print(summary(model))

  # Plot regression
  plot(x, y, main="Linear Regression",
       xlab="X", ylab="Y",
       pch=19, col="blue")
  abline(model, col="red", lwd=2)
  legend("topleft", legend=c("Data", "Regression Line"),
         col=c("blue", "red"), pch=c(19, NA), lty=c(NA, 1))

  cat("\n✓ Statistical analysis complete!\n")
}, error = function(e) {
  cat("✗ Error in statistical analysis:", conditionMessage(e), "\n")
})

# %% [markdown]
# ### 8. Working with Built-in Datasets

# %% vscode={"languageId": "r"}
tryCatch({
  cat(paste0("\n", strrep("=", 60)), "\n")
  cat("Built-in Dataset: iris\n")
  cat(strrep("=", 61), "\n\n")

  # Load iris dataset (built-in)
  data(iris)

  cat("First few rows:\n")
  print(head(iris))

  cat("\nDataset summary:\n")
  print(summary(iris))

  cat("\nSpecies distribution:\n")
  print(table(iris$Species))

  # Create a visualization
  plot(iris$Sepal.Length, iris$Sepal.Width,
       col=iris$Species, pch=19,
       main="Iris: Sepal Length vs Width",
       xlab="Sepal Length", ylab="Sepal Width")
  legend("topright", legend=levels(iris$Species),
         col=1:3, pch=19)

  cat("\n✓ Built-in dataset analysis complete!\n")
}, error = function(e) {
  cat("✗ Error in iris dataset demo:", conditionMessage(e), "\n")
})

# %% [markdown]
# ### 9. Installing Packages (User Library)

# %% vscode={"languageId": "r"}
cat(paste0("\n", strrep("=", 60)), "\n")
cat("Package Installation Demo\n")
cat(strrep("=", 61), "\n\n")

tryCatch({
  cat("This cell demonstrates how to install packages in user space.\n")
  cat("We'll check for a package but not actually install (to save time).\n\n")

  # Example package to check
  example_package <- "jsonlite"

  pkg_available <- tryCatch(
    require(example_package, character.only = TRUE, quietly = TRUE),
    error = function(e) FALSE
  )

  if (pkg_available) {
    cat(sprintf("✓ Package '%s' is already installed\n", example_package))
    tryCatch(
      cat(sprintf("  Version: %s\n", packageVersion(example_package))),
      error = function(e) cat("  (could not retrieve version)\n")
    )
  } else {
    cat(sprintf("✗ Package '%s' is not installed\n\n", example_package))
    cat("To install it in user space, uncomment and run:\n")
    cat(sprintf("  install.packages('%s', lib=.libPaths()[1])\n", example_package))
  }

  cat("\nUser library path:\n")
  cat(" ", .libPaths()[1], "\n")

  cat("\nNote: On shared systems like MetaCentrum, always install to user library!\n")
}, error = function(e) {
  cat("✗ Error in package demo:", conditionMessage(e), "\n")
})

# %% [markdown]
# ## Cleanup
#
# No cleanup needed - this notebook only performs in-memory operations.

# %% vscode={"languageId": "r"}
cat(paste0("\n", strrep("=", 60)), "\n")
cat("Cleanup\n")
cat(strrep("=", 61), "\n\n")

cat("✓ No cleanup needed\n")
cat("\nAll operations were in-memory.\n")
cat("Workspace can be cleared with: rm(list=ls())\n")

# %% [markdown]
# ## Troubleshooting
#
# ### Kernel Issues
#
# **"R_HOME not found" or similar error**
# - R kernel (IRkernel) not installed
# - Install IRkernel from R console (see Prerequisites)
# - Check `jupyter kernelspec list` to see available kernels
#
# **Kernel keeps dying/restarting**
# - R may have crashed due to memory issue
# - Check R error messages in Jupyter console/logs
# - Try smaller datasets or operations
#
# **Can't switch to R kernel**
# - Kernel may not be registered with Jupyter
# - Run from R console: `IRkernel::installspec(user=TRUE)`
# - Restart Jupyter server

# %% [markdown]
# ### Package Issues
#
# **Cannot install packages (permission denied)**
# - Don't have write access to system library
# - Always install to user library: `install.packages('pkg', lib=.libPaths()[1])`
# - Check `.libPaths()` to verify user library exists
#
# **Package installation hangs**
# - Network issue downloading package
# - Try different CRAN mirror: `install.packages('pkg', repos='https://cloud.r-project.org')`
# - Check internet connectivity
#
# **Package won't load (shared object error)**
# - Package requires system libraries
# - May need admin to install system dependencies
# - Try binary packages instead of source

# %% [markdown]
# ### Plotting Issues
#
# **Plots don't appear**
# - May need to explicitly call `plot.new()` or `print()`
# - Check plot output settings in Jupyter
# - Try restarting kernel
#
# **Plot resolution poor**
# - Increase figure size: `options(repr.plot.width=10, repr.plot.height=8)`
# - Adjust before creating plots
#
# **Multiple plots overlap**
# - Reset plot parameters: `par(mfrow=c(1,1))`
# - Clear plot: `dev.off()`

# %% [markdown]
# ### Performance Issues
#
# **R uses too much memory**
# - R loads entire datasets into RAM
# - Use data.table or arrow for large data
# - Clear workspace: `rm(list=ls()); gc()`
#
# **Code runs slowly**
# - Avoid loops, use vectorized operations
# - Profile code with `Rprof()`
# - Consider parallel processing: `parallel` package

# %% [markdown]
# ### Debugging Tips
#
# ```R
# # Check R version
# R.version.string
#
# # List installed packages
# installed.packages()[, c("Package", "Version")]
#
# # Check library paths
# .libPaths()
#
# # Get help on function
# ?mean
# help(plot)
#
# # Search for help
# help.search("regression")
#
# # Check object structure
# str(object)
# class(object)
#
# # Debug function
# debug(my_function)
# # ... run code ...
# undebug(my_function)
# ```

# %% [markdown]
# ## Next Steps
#
# Now that you understand R in Jupyter, you can:
#
# ### Advanced R Usage
#
# - **Tidyverse** - Modern R for data science (dplyr, ggplot2, tidyr)
# - **Data.table** - High-performance data manipulation
# - **Shiny** - Interactive web applications in R
# - **R Markdown** - Mix code and documentation (alternative to notebooks)
# - **Parallel computing** - Use multiple cores with `parallel` package

# %% [markdown]
# ### Statistical & ML Packages
#
# - **caret** - Machine learning framework
# - **randomForest** - Random forest algorithm
# - **glmnet** - Regularized regression
# - **survival** - Survival analysis
# - **forecast** - Time series forecasting
# - **prophet** - Facebook's forecasting tool

# %% [markdown]
# ### Visualization Packages
#
# - **ggplot2** - Grammar of graphics (highly recommended!)
# - **plotly** - Interactive plots
# - **leaflet** - Interactive maps
# - **ggvis** - Interactive graphics

# %% [markdown]
# ### Data Integration
#
# - **DBI + odbc** - Database connections
# - **httr** - HTTP requests (API calls)
# - **jsonlite** - JSON parsing
# - **xml2** - XML parsing
# - **readr** - Fast CSV reading

# %% [markdown]
# ### Multi-language Notebooks
#
# **Mix Python and R**:
# - Use `rpy2` in Python to call R code
# - Use `reticulate` in R to call Python code
# - Share data between languages
#
# **Example workflow**:
# 1. Use Python for data collection (APIs, web scraping)
# 2. Use R for statistical analysis
# 3. Use Python for deployment (web app, ML serving)

# %% [markdown]
# ### Best Practices
#
# **Code organization**:
# - Use functions for reusable code
# - Document with comments
# - Follow style guide (e.g., tidyverse style guide)
#
# **Performance**:
# - Vectorize instead of loops
# - Pre-allocate vectors/lists
# - Use appropriate data structures
# - Profile before optimizing
#
# **Reproducibility**:
# - Set random seed: `set.seed(42)`
# - Document R version: `sessionInfo()`
# - Use `renv` for package management
# - Version control your notebooks

# %% [markdown]
# ### Related Notebooks
#
# - **00_environment_check.ipynb** - Environment detection
# - **07_matlab_kernel_demo.ipynb** - Another alternate kernel example
# - **01_s3_object_storage.ipynb** - Store large R datasets

# %% [markdown]
# ### Documentation
#
# - [R Documentation](https://www.r-project.org/)
# - [IRkernel](https://irkernel.github.io/)
# - [CRAN Task Views](https://cran.r-project.org/web/views/)
# - [R for Data Science](https://r4ds.had.co.nz/)
# - [Advanced R](https://adv-r.hadley.nz/)
# - [Tidyverse](https://www.tidyverse.org/)
# - [RStudio Cheatsheets](https://www.rstudio.com/resources/cheatsheets/)
