from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from backend.api.routes import router


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
FRONTEND_DIRECTORY = PROJECT_DIRECTORY / "frontend"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI-Assisted Data Recovery System",
    description="AI-assisted digital evidence recovery and investigation backend",
    version="1.0.0",
    docs_url="/api-docs",
    redoc_url=None
)


# ============================================================
# ROUTER
# ============================================================

app.include_router(router)


# ============================================================
# CUSTOM OPENAPI
# ============================================================
#
# Fix:
# Swagger was displaying:
#
#     array<string>
#
# instead of:
#
#     Choose Files
#
# FastAPI/OpenAPI 3.1 can represent uploaded binary files using
# contentMediaType. Some Swagger UI versions do not render that
# representation as a file picker.
#
# We convert the upload schema to the OpenAPI 3.0 style:
#
#     type: string
#     format: binary
#
# ============================================================

def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="AI-Assisted Data Recovery System",
        version="1.0.0",
        description="AI-assisted digital evidence recovery and investigation backend",
        routes=app.routes,
    )

    # --------------------------------------------------------
    # Change OpenAPI version
    # --------------------------------------------------------

    openapi_schema["openapi"] = "3.0.3"

    # --------------------------------------------------------
    # Find upload request schema
    # --------------------------------------------------------

    components = openapi_schema.get(
        "components",
        {}
    )

    schemas = components.get(
        "schemas",
        {}
    )

    upload_schema = schemas.get(
        "Body_upload_evidence_api_evidence_upload_post"
    )

    # --------------------------------------------------------
    # Convert files field to Swagger-compatible binary files
    # --------------------------------------------------------

    if upload_schema:

        properties = upload_schema.get(
            "properties",
            {}
        )

        files_schema = properties.get(
            "files"
        )

        if files_schema:

            files_schema.clear()

            files_schema.update({
                "type": "array",
                "title": "Files",
                "description": "Select one or more digital evidence files",
                "items": {
                    "type": "string",
                    "format": "binary"
                }
            })

    # --------------------------------------------------------
    # Store schema
    # --------------------------------------------------------

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    summary="Health Check"
)
async def health_check():

    return {
        "status": "healthy"
    }


# ============================================================
# CUSTOM UPLOAD PAGE
# ============================================================

@app.get(
    "/legacy-docs",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def upload_page():

    return HTMLResponse(
        """
<!DOCTYPE html>

<html>

<head>

    <title>AI-Assisted Data Recovery System</title>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family:
                Arial,
                Helvetica,
                sans-serif;

            background:
                linear-gradient(
                    135deg,
                    #eef2ff,
                    #f8fafc
                );

            color: #1e293b;
        }

        .container {
            max-width: 1100px;
            margin: 50px auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 35px;
        }

        .header h1 {
            margin-bottom: 10px;
            font-size: 34px;
        }

        .header p {
            color: #64748b;
            font-size: 17px;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;

            box-shadow:
                0 10px 30px
                rgba(0, 0, 0, 0.08);
        }

        .card h2 {
            margin-top: 0;
        }

        .upload-area {
            border: 2px dashed #94a3b8;
            border-radius: 12px;
            padding: 35px;
            text-align: center;
            background: #f8fafc;
        }

        input[type="file"] {
            margin: 20px 0;
            width: 100%;
            padding: 15px;
        }

        button {
            border: none;
            border-radius: 8px;
            padding: 13px 24px;

            background: #2563eb;
            color: white;

            font-size: 16px;
            font-weight: bold;

            cursor: pointer;
        }

        button:hover {
            background: #1d4ed8;
        }

        button:disabled {
            background: #94a3b8;
            cursor: not-allowed;
        }

        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            display: none;
        }

        .success {
            background: #dcfce7;
            color: #166534;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
        }

        .investigation {
            display: none;
        }

        .grid {
            display: grid;

            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(200px, 1fr)
                );

            gap: 15px;
            margin-top: 20px;
        }

        .metric {
            padding: 18px;
            background: #f8fafc;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
        }

        .metric-title {
            font-size: 13px;
            color: #64748b;
            margin-bottom: 7px;
        }

        .metric-value {
            font-size: 20px;
            font-weight: bold;
        }

        .explanation {
            margin-top: 20px;
            padding: 20px;
            background: #eff6ff;
            border-left: 5px solid #2563eb;
            border-radius: 8px;
            line-height: 1.6;
        }

        .json-box {
            margin-top: 20px;
            background: #0f172a;
            color: #e2e8f0;

            padding: 20px;

            border-radius: 10px;

            overflow-x: auto;

            white-space: pre-wrap;

            font-family:
                Consolas,
                monospace;

            font-size: 13px;
        }

        .links {
            text-align: center;
            margin-top: 25px;
        }

        .links a {
            color: #2563eb;
            text-decoration: none;
            font-weight: bold;
        }

    </style>

</head>


<body>

<div class="container">


    <!-- =====================================================
         HEADER
    ====================================================== -->

    <div class="header">

        <h1>
            AI-Assisted Data Recovery System
        </h1>

        <p>
            AI-assisted digital evidence recovery
            and investigation backend
        </p>

    </div>


    <!-- =====================================================
         UPLOAD CARD
    ====================================================== -->

    <div class="card">

        <h2>
            Upload Digital Evidence
        </h2>

        <p>
            Upload one or more fragmented evidence files
            for automated analysis and reconstruction.
        </p>


        <div class="upload-area">

            <input
                type="file"
                id="evidenceFiles"
                multiple
            >

            <br>

            <button
                id="uploadButton"
                onclick="uploadEvidence()"
            >
                Analyze Evidence
            </button>

        </div>


        <div
            id="status"
            class="status"
        ></div>

    </div>


    <!-- =====================================================
         INVESTIGATION RESULT
    ====================================================== -->

    <div
        id="investigationCard"
        class="card investigation"
    >

        <h2>
            Investigation Result
        </h2>


        <div
            id="metrics"
            class="grid"
        ></div>


        <div
            id="explanation"
            class="explanation"
        ></div>


        <h3>
            Raw Analysis
        </h3>


        <div
            id="rawJson"
            class="json-box"
        ></div>

    </div>


    <!-- =====================================================
         LINKS
    ====================================================== -->

    <div class="links">

        <a
            href="/api-docs"
            target="_blank"
        >
            Open API Documentation
        </a>

        &nbsp;&nbsp;|&nbsp;&nbsp;

        <a
            href="/health"
            target="_blank"
        >
            Health Check
        </a>

    </div>


</div>


<script>


// ============================================================
// UPLOAD EVIDENCE
// ============================================================

async function uploadEvidence() {

    const fileInput =
        document.getElementById(
            "evidenceFiles"
        );

    const files =
        fileInput.files;


    const status =
        document.getElementById(
            "status"
        );

    const button =
        document.getElementById(
            "uploadButton"
        );


    if (!files.length) {

        status.style.display = "block";

        status.className =
            "status error";

        status.textContent =
            "Please select one or more evidence files.";

        return;
    }


    const formData =
        new FormData();


    for (
        let i = 0;
        i < files.length;
        i++
    ) {

        formData.append(
            "files",
            files[i]
        );

    }


    button.disabled = true;

    button.textContent =
        "Analyzing Evidence...";


    status.style.display = "block";

    status.className =
        "status";

    status.style.background =
        "#e0f2fe";

    status.style.color =
        "#075985";

    status.textContent =
        "Uploading and analyzing evidence...";


    try {

        const response =
            await fetch(
                "/api/evidence/upload",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Evidence analysis failed."
            );

        }


        status.className =
            "status success";

        status.style.display =
            "block";

        status.textContent =
            "Evidence analyzed successfully.";


        displayInvestigation(
            data
        );


    }
    catch (error) {

        status.className =
            "status error";

        status.style.display =
            "block";

        status.textContent =
            error.message;

    }
    finally {

        button.disabled =
            false;

        button.textContent =
            "Analyze Evidence";

    }

}


// ============================================================
// DISPLAY INVESTIGATION
// ============================================================

function displayInvestigation(
    data
) {

    const investigation =
        data.investigation ||
        {};


    const card =
        document.getElementById(
            "investigationCard"
        );


    const metrics =
        document.getElementById(
            "metrics"
        );


    const explanation =
        document.getElementById(
            "explanation"
        );


    const rawJson =
        document.getElementById(
            "rawJson"
        );


    card.style.display =
        "block";


    metrics.innerHTML = `

        <div class="metric">

            <div class="metric-title">
                Recovery Status
            </div>

            <div class="metric-value">
                ${investigation.status || "UNKNOWN"}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                File Type
            </div>

            <div class="metric-value">
                ${investigation.file_type || "UNKNOWN"}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                Artifact
            </div>

            <div class="metric-value">
                ${investigation.artifact_category || "UNKNOWN"}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                Fragments Used
            </div>

            <div class="metric-value">
                ${investigation.fragments_used ?? 0}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                Ordering Confidence
            </div>

            <div class="metric-value">
                ${investigation.ordering_confidence ?? 0}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                Reconstruction
            </div>

            <div class="metric-value">
                ${investigation.reconstruction_status || "UNKNOWN"}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                Integrity
            </div>

            <div class="metric-value">
                ${investigation.integrity_status || "UNKNOWN"}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                Corruption
            </div>

            <div class="metric-value">
                ${investigation.corruption_status || "UNKNOWN"}
            </div>

        </div>


        <div class="metric">

            <div class="metric-title">
                Priority
            </div>

            <div class="metric-value">
                ${investigation.priority || "UNKNOWN"}
                (${investigation.priority_score ?? 0}/100)
            </div>

        </div>

    `;


    explanation.innerHTML = `

        <strong>
            AI / Forensic Explanation
        </strong>

        <br><br>

        ${
            investigation.explanation ||
            "No explanation available."
        }

        <br><br>

        <strong>
            Fragment Order:
        </strong>

        <br>

        ${
            (
                investigation.fragment_order ||
                []
            ).join(" → ") ||
            "Not available"
        }

    `;


    rawJson.textContent =
        JSON.stringify(
            data,
            null,
            2
        );

}


</script>


</body>

</html>
        """
    )


# ============================================================
# INTERACTIVE FRONTEND
# ============================================================

@app.get("/", include_in_schema=False)
@app.get("/ui", include_in_schema=False)
@app.get("/docs", include_in_schema=False)
async def interactive_frontend():
    """Serve the primary browser workspace for evidence recovery."""

    return FileResponse(
        FRONTEND_DIRECTORY / "index.html"
    )


app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIRECTORY),
    name="frontend"
)
