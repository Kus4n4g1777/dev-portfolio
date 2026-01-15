package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/generative-ai-go/genai"
	"google.golang.org/api/option"
)

type PromptRequest struct {
	Prompt string `json:"prompt" binding:"required"`
}

type HealthResponse struct {
	Status  string `json:"status"`
	Runtime string `json:"runtime"`
}

type GenerateResponse struct {
	Runtime  string  `json:"runtime"`
	Model    string  `json:"model"`
	Response *string `json:"response"`
	Error    *string `json:"error"`
}

var geminiClient *genai.Client

func main() {
	// Initialize Gemini client
	apiKey := os.Getenv("GEMINI_API_KEY")
	if apiKey == "" {
		log.Println("WARNING: GEMINI_API_KEY not set")
	} else {
		ctx := context.Background()
		var err error
		geminiClient, err = genai.NewClient(ctx, option.WithAPIKey(apiKey))
		if err != nil {
			log.Fatalf("Failed to create Gemini client: %v", err)
		}
		defer geminiClient.Close()
	}

	// Setup Gin router
	r := gin.Default()

	// Routes
	r.GET("/", rootHandler)
	r.GET("/health", healthHandler)
	r.POST("/generate", generateHandler)

	// Get port from env or default
	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}

	log.Printf("🚀 Starting Go Runtime Service on port %s\n", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func rootHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"service": "Go Runtime Service",
		"version": "1.0.0",
		"runtime": "Go",
	})
}

func healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, HealthResponse{
		Status:  "healthy",
		Runtime: "go",
	})
}

func generateHandler(c *gin.Context) {
	var req PromptRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		errMsg := "prompt is required"
		c.JSON(http.StatusBadRequest, GenerateResponse{
			Runtime:  "go",
			Model:    "",
			Response: nil,
			Error:    &errMsg,
		})
		return
	}

	if geminiClient == nil {
		errMsg := "GEMINI_API_KEY not configured"
		c.JSON(http.StatusInternalServerError, GenerateResponse{
			Runtime:  "go",
			Model:    "",
			Response: nil,
			Error:    &errMsg,
		})
		return
	}

	// Generate content using Gemini
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	model := geminiClient.GenerativeModel("gemini-2.5-flash")
	resp, err := model.GenerateContent(ctx, genai.Text(req.Prompt))

	if err != nil {
		errMsg := err.Error()
		c.JSON(http.StatusInternalServerError, GenerateResponse{
			Runtime:  "go",
			Model:    "gemini-2.5-flash",
			Response: nil,
			Error:    &errMsg,
		})
		return
	}

	// Extract text from response
	var responseText string
	if len(resp.Candidates) > 0 && len(resp.Candidates[0].Content.Parts) > 0 {
		responseText = fmt.Sprintf("%v", resp.Candidates[0].Content.Parts[0])
	}

	c.JSON(http.StatusOK, GenerateResponse{
		Runtime:  "go",
		Model:    "gemini-2.5-flash",
		Response: &responseText,
		Error:    nil,
	})
}
