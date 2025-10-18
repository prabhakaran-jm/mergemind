# MergeMind Architecture Documentation

This directory contains comprehensive architecture diagrams for the MergeMind platform, created using PlantUML for detailed technical documentation.

## 📊 Architecture Diagrams

### 1. [ARCHITECTURE_DIAGRAM.puml](ARCHITECTURE_DIAGRAM.puml)
**Complete System Architecture**

This diagram shows the full system architecture including:
- **Data Sources**: GitLab API and Fivetran Connector
- **Event-Driven Pipeline**: Cloud Function and dbt transformations
- **Data Warehouse**: BigQuery raw and modeled datasets
- **AI Services Layer**: All AI services and Vertex AI integration
- **API Layer**: FastAPI backend with all routers
- **Frontend Layer**: React components and UI structure
- **Infrastructure**: Google Cloud Platform services

**Key Features:**
- Detailed component descriptions
- Service relationships and data flow
- Security and credential management
- Production-ready infrastructure

### 2. [DATA_FLOW_DIAGRAM.puml](DATA_FLOW_DIAGRAM.puml)
**Event-Driven Pipeline Flow**

This diagram illustrates the complete data flow from GitLab events to user interface:
- **GitLab Events**: MR creation, updates, comments
- **Fivetran Sync**: Incremental data ingestion
- **Cloud Function Trigger**: Automated dbt execution
- **Data Transformation**: Raw to modeled data
- **AI Processing**: Analysis and insights generation
- **Frontend Display**: Real-time dashboard updates

**Key Features:**
- Step-by-step process flow
- Error handling and retry logic
- Performance characteristics
- Parallel processing paths

### 3. [DEPLOYMENT_ARCHITECTURE.puml](DEPLOYMENT_ARCHITECTURE.puml)
**Production Deployment Structure**

This diagram shows the production deployment architecture:
- **Cloud Run Services**: API and UI services
- **Cloud Functions**: dbt trigger function
- **BigQuery**: Data warehouse setup
- **Vertex AI**: AI services integration
- **Secret Manager**: Credential management
- **Cloud Storage**: State and source code storage
- **Monitoring**: Logging, metrics, and alerting

**Key Features:**
- Production service configurations
- Security and access control
- Monitoring and observability
- External service integrations

## 🛠️ How to View These Diagrams

### Option 1: Online PlantUML Viewer
1. Copy the content of any `.puml` file
2. Go to [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
3. Paste the content and view the rendered diagram

### Option 2: VS Code Extension
1. Install the "PlantUML" extension in VS Code
2. Open any `.puml` file
3. Use `Ctrl+Shift+P` → "PlantUML: Preview Current Diagram"

### Option 3: Local PlantUML Installation
```bash
# Install PlantUML
npm install -g node-plantuml

# Generate PNG from PUML
puml generate ARCHITECTURE_DIAGRAM.puml --png

# Generate SVG from PUML
puml generate ARCHITECTURE_DIAGRAM.puml --svg
```

### Option 4: IntelliJ IDEA Plugin
1. Install "PlantUML integration" plugin
2. Open `.puml` files directly in IntelliJ
3. Diagrams render automatically

## 📋 Diagram Maintenance

### When to Update Diagrams
- **New Services**: Add new components or services
- **Architecture Changes**: Modify system structure
- **Deployment Updates**: Change infrastructure setup
- **API Changes**: Update endpoint or service relationships

### Best Practices
- Keep diagrams synchronized with actual implementation
- Use consistent naming conventions
- Include relevant technical details in notes
- Update diagrams during major releases

## 🔗 Related Documentation

- [README.md](../README.md) - Main project documentation
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Deployment guide
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation

## 📝 Contributing

When updating architecture diagrams:
1. Ensure diagrams reflect actual implementation
2. Test diagrams render correctly in PlantUML viewer
3. Update this README if adding new diagrams
4. Follow consistent styling and formatting

---

**Note**: These diagrams are automatically generated from PlantUML source files. Always edit the `.puml` files, not the rendered images.
