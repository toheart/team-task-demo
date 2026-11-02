package wire

import (
	"log/slog"

	appsample "github.com/toheart/team-task-demo/backend/internal/application/sample"
	"github.com/toheart/team-task-demo/backend/internal/infrastructure/storage/memory"
	httpserver "github.com/toheart/team-task-demo/backend/internal/interfaces/http"
	"github.com/toheart/team-task-demo/backend/internal/interfaces/http/handler"

	"github.com/toheart/team-task-demo/backend/conf"
)

func BuildHTTPServer(cfg conf.Config, logger *slog.Logger) *httpserver.Server {
	repo := memory.NewSampleRepository()
	service := appsample.NewService(repo)
	sampleHandler := handler.NewSampleHandler(service)

	return httpserver.New(cfg, logger, sampleHandler)
}
