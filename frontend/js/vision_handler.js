/**
 * ORION Vision and Image Input Handler
 * Manages equipment photograph uploads, meter dial scans, and OCR previews.
 */

class VisionHandler {
  constructor() {
    this.dropzone = document.getElementById('image-dropzone');
    this.fileInput = document.getElementById('image-file-input');
    this.browseLink = document.getElementById('browse-image-link');
    this.idleView = document.getElementById('dropzone-idle');
    this.previewView = document.getElementById('dropzone-preview');
    this.previewImg = document.getElementById('image-preview-elem');
    this.previewFilename = document.getElementById('preview-filename');
    this.clearBtn = document.getElementById('btn-clear-img');

    this.currentFile = null;
    this.initEvents();
  }

  initEvents() {
    if (this.browseLink && this.fileInput) {
      this.browseLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.fileInput.click();
      });
    }

    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          this.handleFile(e.target.files[0]);
        }
      });
    }

    if (this.dropzone) {
      ['dragenter', 'dragover'].forEach(eventName => {
        this.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          this.dropzone.style.borderColor = 'var(--border-bright)';
          this.dropzone.style.background = 'rgba(56, 189, 248, 0.08)';
        });
      });

      ['dragleave', 'drop'].forEach(eventName => {
        this.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          this.dropzone.style.borderColor = '';
          this.dropzone.style.background = '';
        });
      });

      this.dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.handleFile(e.dataTransfer.files[0]);
        }
      });
    }

    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clearImage();
      });
    }
  }

  handleFile(file) {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file (PNG, JPG, WEBP).');
      return;
    }

    this.currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      this.previewImg.src = e.target.result;
      this.previewFilename.textContent = file.name;
      this.idleView.style.display = 'none';
      this.previewView.style.display = 'block';
      window.showToast?.(`Equipment photo '${file.name}' attached for OCR.`);
    };
    reader.readAsDataURL(file);
  }

  clearImage() {
    this.currentFile = null;
    this.previewImg.src = '';
    this.fileInput.value = '';
    this.previewView.style.display = 'none';
    this.idleView.style.display = 'block';
  }

  getImageFile() {
    return this.currentFile;
  }
}

window.VisionHandler = VisionHandler;
