// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FlashloanArbitrage (EDUCATIONAL)
 * @notice Illustrates an Aave V3 flashloan callback that would:
 *         1) borrow asset
 *         2) swap on DEX A
 *         3) swap back on DEX B
 *         4) repay + premium
 *
 * WARNING
 * -------
 * - Not audited. Not production-ready.
 * - Router addresses / calldata must be supplied carefully.
 * - On-chain arb is fiercely competitive; most naive bots lose money on gas.
 * - Do NOT use this to attack or drain protocols.
 */

interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

interface IPoolAddressesProvider {
    function getPool() external view returns (address);
}

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
}

interface ISwapRouterMinimal {
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);
}

contract FlashloanArbitrage {
    address public owner;
    IPoolAddressesProvider public immutable ADDRESSES_PROVIDER;

    error NotOwner();
    error InvalidInitiator();
    error Unprofitable();

    struct ArbParams {
        address routerBuy;
        address routerSell;
        address tokenBorrowed;
        address tokenMid;
        uint256 minOutBuy;
        uint256 minOutSell;
        uint256 deadline;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(address addressesProvider) {
        owner = msg.sender;
        ADDRESSES_PROVIDER = IPoolAddressesProvider(addressesProvider);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }

    /// @notice Kick off a flashloan. `params` ABI-encodes ArbParams.
    function startArbitrage(
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyOwner {
        address pool = ADDRESSES_PROVIDER.getPool();
        IPool(pool).flashLoanSimple(address(this), asset, amount, params, 0);
    }

    /**
     * @dev Aave V3 flashloan callback.
     *      Must approve/repay `amount + premium` before returning true.
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        address pool = ADDRESSES_PROVIDER.getPool();
        if (msg.sender != pool || initiator != address(this)) revert InvalidInitiator();

        ArbParams memory p = abi.decode(params, (ArbParams));
        require(p.tokenBorrowed == asset, "asset mismatch");

        // 1) Borrowed asset → mid token on cheaper venue
        IERC20(asset).approve(p.routerBuy, amount);
        address[] memory pathBuy = new address[](2);
        pathBuy[0] = p.tokenBorrowed;
        pathBuy[1] = p.tokenMid;
        ISwapRouterMinimal(p.routerBuy).swapExactTokensForTokens(
            amount,
            p.minOutBuy,
            pathBuy,
            address(this),
            p.deadline
        );

        uint256 midBal = IERC20(p.tokenMid).balanceOf(address(this));

        // 2) Mid token → borrowed asset on richer venue
        IERC20(p.tokenMid).approve(p.routerSell, midBal);
        address[] memory pathSell = new address[](2);
        pathSell[0] = p.tokenMid;
        pathSell[1] = p.tokenBorrowed;
        ISwapRouterMinimal(p.routerSell).swapExactTokensForTokens(
            midBal,
            p.minOutSell,
            pathSell,
            address(this),
            p.deadline
        );

        uint256 owed = amount + premium;
        uint256 endBal = IERC20(asset).balanceOf(address(this));
        if (endBal < owed) revert Unprofitable();

        IERC20(asset).approve(pool, owed);

        uint256 profit = endBal - owed;
        if (profit > 0) {
            IERC20(asset).transfer(owner, profit);
        }
        return true;
    }

    /// @notice Rescue tokens stuck in the contract.
    function rescue(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner, amount);
    }
}
