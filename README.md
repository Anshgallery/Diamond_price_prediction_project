# Diamond Price Prediction

<img src="images/diamond-price-prediction.png" alt="Diamond Price Prediction Application" width="100%">

> An end-to-end Machine Learning application for diamond price prediction, featuring modular ML pipeline architecture, automated data transformation, model training and evaluation, Flask-based inference, Docker containerization, GitHub Actions CI/CD, Azure Container Registry, and Azure Web App deployment.

---


## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [System Architecture](#system-architecture)
- [ML Pipeline Architecture](#ml-pipeline-architecture)
- [Application Workflow](#application-workflow)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Dataset](#dataset)
- [Data Preprocessing](#data-preprocessing)
- [Feature Engineering](#feature-engineering)
- [Model Training](#model-training)
- [Model Evaluation](#model-evaluation)
- [Prediction Pipeline](#prediction-pipeline)
- [Web Application](#web-application)
- [Dockerization](#dockerization)
- [CI/CD Pipeline](#cicd-pipeline)
- [Azure Deployment](#azure-deployment)
- [Environment Configuration](#environment-configuration)
- [Local Development](#local-development)
- [Docker Execution](#docker-execution)
- [CI/CD Deployment Flow](#cicd-deployment-flow)
- [Security](#security)
- [Future Improvements](#future-improvements)
- [Key Learnings](#key-learnings)
- [Author](#author)

---

# Overview

Diamond Price Prediction is an end-to-end Machine Learning application designed to estimate the price of a diamond based on its physical and quality-related characteristics.

The project follows a modular Machine Learning architecture in which individual components are separated into dedicated pipeline stages for data ingestion, data transformation, model training, model evaluation, and prediction.

The trained model is integrated with a Flask web application that provides a user-facing interface for generating real-time predictions.

The application is containerized using Docker and deployed through an automated CI/CD pipeline using GitHub Actions.

The deployment architecture uses:

- Azure Container Registry (ACR) for Docker Image storage
- Azure Web App for cloud application hosting
- GitHub Actions for CI/CD automation

---

# Problem Statement

Diamond pricing depends on multiple characteristics related to quality, physical dimensions, and grading standards.

Determining an appropriate price manually can be difficult because the relationship between these variables is not always linear.

The objective of this project is to develop a Machine Learning regression system capable of learning patterns from historical diamond data and predicting the expected price of a new diamond based on its attributes.

The project addresses the following workflow:

```text
Historical Diamond Data
          |
          v
Data Preprocessing
          |
          v
Feature Transformation
          |
          v
Model Training
          |
          v
Model Evaluation
          |
          v
Best Model Selection
          |
          v
Prediction Pipeline
          |
          v
Flask Web Application
          |
          v
Docker Container
          |
          v
Cloud Deployment
