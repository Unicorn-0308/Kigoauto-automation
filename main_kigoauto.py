import requests
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from kigoauto_automation import KigoAutoLogin
import json
import traceback
from typing import Optional

# Initialize KigoAutoLogin with error handling
kigo = None
try:
    kigo = KigoAutoLogin(headless=False)
    print("KigoAutoLogin initialized successfully")
except Exception as e:
    print(f"Warning: Failed to initialize KigoAutoLogin on startup: {str(e)}")
    print("Will attempt to initialize on first request")

# Global variables for session management
cart_token = ""
cookies = {}
session_cookies = []

# FastAPI app
app = FastAPI(title="KigoAuto Automation API", version="1.0.0")

class Account(BaseModel):
    email: str
    password: str

class Product(BaseModel):
    url: str
    quantity: int = 1

class LoginResponse(BaseModel):
    status: str
    message: Optional[str] = None
    cookies: Optional[dict] = None
    cart_token: Optional[str] = None

class ProductResponse(BaseModel):
    status: str
    message: str
    cart_token: Optional[str] = None
    cookies: Optional[dict] = None

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {
        "message": "KigoAuto Automation API is running",
        "endpoints": {
            "/login": "POST - Login to KigoAuto",
            "/add-product": "POST - Add product to cart",
            "/get-cookies": "GET - Get current session cookies",
            "/update-cookies": "POST - Update session cookies",
            "/cart-status": "GET - Get cart status",
            "/close-browser": "POST - Close browser and cleanup"
        }
    }

@app.post("/login", response_model=LoginResponse)
async def login(account: Account):
    """Login to KigoAuto.com and retrieve session cookies"""
    global cart_token, cookies, session_cookies, kigo
    
    # Initialize KigoAutoLogin if not already done
    if kigo is None:
        try:
            kigo = KigoAutoLogin(headless=False)
            print("KigoAutoLogin initialized on demand")
        except Exception as e:
            error_msg = f"Failed to initialize WebDriver: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return LoginResponse(
                status="fail",
                message=error_msg
            )
    
    try:
        print(f"Attempting login for: {account.email}")
        
        # Perform login
        if kigo.login(account.email, account.password):
            # Get cookies from the browser
            session_cookies = kigo.get_cookies()
            
            # Process cookies into a dictionary
            cookies = {}
            for cookie in session_cookies:
                cookies[cookie["name"]] = cookie["value"]
                # Look for cart-related cookies
                if "cart" in cookie["name"].lower():
                    cart_token = cookie["value"]
            
            # Save cookies to file for backup
            kigo.save_cookies_to_file("kigoauto_session.json")
            
            print(f"Login successful. Retrieved {len(cookies)} cookies")
            
            return LoginResponse(
                status="success",
                message="Login successful",
                cookies=cookies,
                cart_token=cart_token
            )
        else:
            return LoginResponse(
                status="fail",
                message="Login failed. Please check credentials."
            )
            
    except Exception as e:
        error_msg = f"Login error: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return LoginResponse(
            status="error",
            message=error_msg
        )

@app.post("/add-product", response_model=ProductResponse)
async def add_product(product: Product):
    """Add a product to the cart"""
    global kigo, cart_token, cookies
    
    # Check if KigoAutoLogin is initialized
    if kigo is None:
        return ProductResponse(
            status="fail",
            message="Not logged in. Please login first."
        )
    
    try:
        print(f"Adding product: {product.url} with quantity: {product.quantity}")
        
        # Add product to cart
        if kigo.add_products(product.url, product.quantity):
            # Get updated cookies
            updated_cookies = kigo.get_cookies()
            
            # Update global cookies
            cookies = {}
            for cookie in updated_cookies:
                cookies[cookie["name"]] = cookie["value"]
                if "cart" in cookie["name"].lower():
                    cart_token = cookie["value"]
            
            # Optional: Auto-close browser after adding to cart
            # Uncomment the following lines if you want to auto-close
            print("Auto-closing browser after adding to cart...")
            kigo.close()
            kigo = None
            
            return ProductResponse(
                status="success",
                message=f"Successfully added {product.quantity} item(s) to cart",
                cart_token=cart_token,
                cookies=cookies
            )
        else:
            return ProductResponse(
                status="fail",
                message="Failed to add product to cart"
            )
            
    except Exception as e:
        error_msg = f"Error adding product: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return ProductResponse(
            status="error",
            message=error_msg
        )

@app.get("/get-cookies")
async def get_cookies():
    """Get current session cookies"""
    global cookies, cart_token
    
    if not cookies:
        return {
            "status": "fail",
            "message": "No active session. Please login first."
        }
    
    return {
        "status": "success",
        "cookies": cookies,
        "cart_token": cart_token,
        "total_cookies": len(cookies)
    }

@app.post("/update-cookies")
async def update_cookies():
    """Update cookies from current browser session"""
    global kigo, cookies, cart_token
    
    if kigo is None:
        return {
            "status": "fail",
            "message": "Not logged in. Please login first."
        }
    
    try:
        # Get current cookies from browser
        current_cookies = kigo.get_cookies()
        
        # Update global cookies
        cookies = {}
        for cookie in current_cookies:
            cookies[cookie["name"]] = cookie["value"]
            if "cart" in cookie["name"].lower():
                cart_token = cookie["value"]
        
        return {
            "status": "success",
            "message": "Cookies updated successfully",
            "cookies": cookies,
            "cart_token": cart_token
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update cookies: {str(e)}"
        }

@app.get("/cart-status")
async def cart_status():
    """Get current cart status"""
    global kigo, cart_token
    
    if kigo is None:
        return {
            "status": "fail",
            "message": "Not logged in. Please login first."
        }
    
    try:
        # Navigate to cart page
        kigo.driver.get("http://kigoauto.com/cart")
        kigo.human_like_delay(2, 3)
        
        # Try to find cart items or total
        cart_info = {
            "status": "success",
            "cart_url": kigo.driver.current_url,
            "cart_token": cart_token
        }
        
        # Look for cart item count
        try:
            cart_count_selectors = [
                ".cart-count",
                ".cart-item-count",
                ".cart-qty",
                "[data-cart-count]"
            ]
            
            from selenium.webdriver.common.by import By
            for selector in cart_count_selectors:
                try:
                    element = kigo.driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        cart_info["item_count"] = element.text
                        break
                except:
                    continue
        except:
            pass
        
        return cart_info
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get cart status: {str(e)}"
        }

@app.post("/close-browser")
async def close_browser():
    """Close the browser and cleanup resources"""
    global kigo, cart_token, cookies
    
    if kigo is None:
        return {
            "status": "info",
            "message": "No browser session to close"
        }
    
    try:
        # Close the browser
        kigo.close()
        
        # Reset the global variables
        kigo = None
        cart_token = ""
        cookies = {}
        
        return {
            "status": "success",
            "message": "Browser closed successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to close browser: {str(e)}"
        }

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    global kigo
    if kigo:
        try:
            kigo.close()
            print("Browser closed and cleanup completed")
        except:
            pass

# Run the application
if __name__ == "__main__":
    import uvicorn
    print("Starting KigoAuto Automation API...")
    print("Access the API at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
