const crypto = require('crypto');

// Simple session storage (in production, use Redis or similar)
const sessions = new Map();

// Hash password with SHA-256
function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

// Generate session token
function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}

// Create session
function createSession(userId, userEmail, userRole, orgId) {
  const token = generateToken();
  sessions.set(token, {
    userId,
    userEmail,
    userRole,
    orgId,
    createdAt: Date.now()
  });
  return token;
}

// Verify session
function verifySession(token) {
  const session = sessions.get(token);
  if (!session) return null;

  // Session expires after 24 hours
  const age = Date.now() - session.createdAt;
  if (age > 24 * 60 * 60 * 1000) {
    sessions.delete(token);
    return null;
  }

  return session;
}

// Middleware to require authentication
function requireAuth(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '') || req.cookies?.token;

  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  const session = verifySession(token);
  if (!session) {
    return res.status(401).json({ error: 'Invalid or expired session' });
  }

  req.user = session;
  next();
}

// Middleware to require specific role
function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    if (!roles.includes(req.user.userRole)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }

    next();
  };
}

// Logout
function logout(token) {
  sessions.delete(token);
}

module.exports = {
  hashPassword,
  createSession,
  verifySession,
  requireAuth,
  requireRole,
  logout
};
