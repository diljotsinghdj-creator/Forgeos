"""A Civitai checkpoint (one .safetensors file) is loaded as an SDXL model with the SDXL settings."""
from creatorforge_worker.providers import _downloaded
from creatorforge_worker.providers.image_diffusers import DiffusersImageProvider


def test_single_file_checkpoint_is_treated_as_sdxl(tmp_path):
    p = DiffusersImageProvider(str(tmp_path / "789646.safetensors"))
    assert p.single_file and p.sdxl and p.hires and p.steps == 25
    flux = DiffusersImageProvider("black-forest-labs/FLUX.1-schnell")
    assert not flux.single_file and not flux.sdxl and flux.steps == 4


def test_a_civitai_file_counts_as_downloaded_only_when_complete(tmp_path):
    f = tmp_path / "1.safetensors"
    assert not _downloaded(str(f))
    f.write_bytes(b"x" * 1000)
    assert not _downloaded(str(f))          # a partial or tiny file is not a model
