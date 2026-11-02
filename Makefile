.PHONY: dev dev-backend dev-frontend check clean

dev:
	@echo "Starting backend (:8080) and frontend (:3000)..."
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	@cd backend && make run

dev-frontend:
	@cd frontend && npm run dev

check:
	@cd backend && make check
	@cd frontend && npm run lint && npm test && npm run build

clean:
	@rm -rf backend/bin frontend/dist
