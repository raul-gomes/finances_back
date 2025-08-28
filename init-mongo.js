db = db.getSiblingDB('admin');

try {
  rs.status();
} catch (e) {
  rs.initiate({
    _id: "rs0",
    members: [{ _id: 0, host: "mongo:27017" }]
  });
  // Aguarda o replica set iniciar
  sleep(5000);
}

