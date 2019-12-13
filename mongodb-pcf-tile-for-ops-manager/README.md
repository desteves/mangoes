# MongoDB Ops Manager PCF Tile

MongoDB Ops Manager PCF Tile for MongoDB Ops Manager 4.0.x

**THIS IS A STANDALONE INSTANCE WITH NO BACKUPS or HTTPS CONFIGURED, FOR DEV ONLY**

See [this](https://github.com/desteves/mms-bosh-release) github repo for the BOSH release.

## Build

- Ensure the BOSH release is in `release/` folder.
- Update the `tile.yml` accordingly.
- To compile the `.pivotal` file run `tile build`.

Example,

```bash
BOSH_RELEASE_DIR=~/git/release
TILE_DIR=~/git/tile

cd ${BOSH_RELEASE_DIR}
bosh create-release --json --final --tarball ${TILE_DIR}/release/mms.tgz --name mms | tee /tmp/create.json
cd ${TILE_DIR}
tile build
```
